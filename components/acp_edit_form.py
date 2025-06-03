from fasthtml.common import *
import json
import os
import asyncio
from typing import Dict, List, Any
from dotenv import load_dotenv
import openai
from datetime import datetime

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

class LessonGeneratorForm:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.reasoning_model = "o4-mini"
        self.non_reasoning_model = "gpt-4o-mini-2024-07-18"
    
    def create_lesson_input_form(self):
        """Create the initial lesson details input form"""
        return Div(
            Card(
                Header(
                    H2("🎓 Lesson Generator", cls="text-center", style="color: white;"),
                    P("Create comprehensive lesson plans with AI assistance", cls="text-center text-muted", style="color: #e5e7eb;"),
                    cls="pb-4",
                    style="background-color: #1e3a8a; padding: 1rem; margin: -1rem -1rem 1rem -1rem; border-radius: 6px 6px 0 0;"
                ),
                Form(
                    # Model Selection
                    Div(
                        Label("AI Model Selection:", cls="font-weight-bold", style="color: #495057;"),
                        Div(
                            Label(
                                Input(type="radio", name="model_type", value="reasoning", checked=True),
                                " Reasoning Model (o4-mini) - More thoughtful planning",
                                cls="form-check-label",
                                style="color: #495057;"
                            ),
                            Label(
                                Input(type="radio", name="model_type", value="non_reasoning"),
                                " Standard Model (gpt-4o-mini) - Faster generation",
                                cls="form-check-label",
                                style="color: #495057;"
                            ),
                            cls="form-check-container"
                        ),
                        cls="mb-4 p-3 border rounded"
                    ),
                    
                    # Lesson Details
                    Grid(
                        Div(
                            Label("Lesson Title:", style="color: #495057;"),
                            Input(name="lesson_title", placeholder="e.g., Introduction to Photosynthesis", required=True)
                        ),
                        Div(
                            Label("Subject:", style="color: #495057;"),
                            Input(name="subject", placeholder="e.g., Biology, Chemistry, Math", required=True)
                        ),
                        Div(
                            Label("Topic:", style="color: #495057;"),
                            Input(name="topic", placeholder="e.g., Cellular processes", required=True)
                        ),
                        Div(
                            Label("Level/Grade:", style="color: #495057;"),
                            Input(name="level_grade", placeholder="e.g., Secondary 2, Grade 9", required=True)
                        ),
                        cls="grid-cols-2 gap-4 mb-4"
                    ),
                    
                    Div(
                        Label("Additional Instructions (Optional):", style="color: #495057;"),
                        Textarea(
                            name="additional_instructions",
                            placeholder="Any specific requirements, learning objectives, or teaching approaches...",
                            rows=3
                        ),
                        cls="mb-4"
                    ),
                    
                    # Lesson Structure
                    Grid(
                        Div(
                            Label("Number of Sections:", style="color: #495057;"),
                            Select(
                                Option("1", value="1"),
                                Option("2", value="2", selected=True),
                                Option("3", value="3"),
                                Option("4", value="4"),
                                Option("5", value="5"),
                                name="num_sections"
                            )
                        ),
                        Div(
                            Label("Activities per Section:", style="color: black;"),
                            Select(
                                Option("1", value="1"),
                                Option("2", value="2", selected=True),
                                Option("3", value="3"),
                                Option("4", value="4"),
                                Option("5", value="5"),
                                name="max_activities"
                            )
                        ),
                        cls="grid-cols-2 gap-4 mb-4"
                    ),
                    
                    Button(
                        "🚀 Generate High-Level Plan",
                        type="submit",
                        hx_post="/api/lesson/generate-plan",
                        hx_target="#lesson-content",
                        hx_swap="innerHTML",
                        hx_indicator="#loading-indicator",
                        cls="btn-primary w-full"
                    ),
                    
                    id="lesson-form"
                ),
                cls="p-4",
                style="background-color: #1e3a8a;"
            ),
            
            # Loading indicator
            Div(
                Div(cls="spinner"),
                P("Generating your lesson plan...", cls="loading-text"),
                id="loading-indicator",
                cls="loading-container htmx-indicator"
            ),
            
            # Content area for results
            Div(id="lesson-content", cls="mt-4"),
            
            # Add CSS styles
            Style("""
                .container {
                    background-color: #6b7280 !important;
                }
                body {
                    background-color: #6b7280 !important;
                }
                .form-check-container {
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                }
                .form-check-label {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    cursor: pointer;
                }
                .loading-container {
                    text-align: center;
                    padding: 2rem;
                    display: none;
                }
                .loading-container.htmx-indicator.htmx-request {
                    display: block;
                }
                .spinner {
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #667eea;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 1rem;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                .loading-text {
                    color: #667eea;
                    font-weight: 500;
                }
                .btn-primary {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    color: white;
                    padding: 0.75rem 1.5rem;
                    border-radius: 6px;
                    font-weight: 500;
                    transition: transform 0.2s ease;
                }
                .btn-primary:hover {
                    transform: translateY(-2px);
                }
            """),
            
            cls="container mx-auto max-w-4xl p-4"
        )
    
    def _format_lesson_plan_content(self, content: str) -> str:
        """Format the lesson plan content with proper HTML structure"""
        if not content:
            return ""
        
        # Split content into lines and process
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('<br>')
                continue
            
            # Handle main headings with **
            if line.startswith('**') and line.endswith('**'):
                heading_text = line.replace('**', '').strip()
                if heading_text.endswith(':'):
                    heading_text = heading_text[:-1]
                formatted_lines.append(f'<h4 style="color: #fbbf24; margin-top: 1.5rem; margin-bottom: 0.75rem; font-weight: bold; border-bottom: 2px solid #fbbf24; padding-bottom: 0.25rem;">{heading_text}</h4>')
            
            # Handle numbered points (1., 2., etc.)
            elif line.startswith(('1. ', '2. ', '3. ', '4. ', '5. ')):
                formatted_lines.append(f'<div style="margin-left: 1rem; margin-bottom: 0.75rem;"><strong style="color: #fbbf24;">{line[:2]}</strong> {line[3:]}</div>')
            
            # Handle bullet points with •
            elif line.startswith('• '):
                formatted_lines.append(f'<div style="margin-left: 2rem; margin-bottom: 0.5rem; color: #e5e7eb;">• {line[2:]}</div>')
            
            # Handle section titles (no ** but followed by specific patterns)
            elif (':' in line and not line.startswith('-') and len(line.split(':')[0]) < 50):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    formatted_lines.append(f'<div style="margin-top: 1rem; margin-bottom: 0.5rem;"><strong style="color: #60a5fa;">{parts[0]}:</strong> {parts[1]}</div>')
                else:
                    formatted_lines.append(f'<div style="margin-bottom: 0.5rem; line-height: 1.6;">{line}</div>')
            
            # Handle sub-points with -
            elif line.startswith('- '):
                formatted_lines.append(f'<div style="margin-left: 1rem; margin-bottom: 0.5rem; color: #e5e7eb;">- {line[2:]}</div>')
            
            # Regular text
            else:
                formatted_lines.append(f'<div style="margin-bottom: 0.75rem; line-height: 1.6;">{line}</div>')
        
        return ''.join(formatted_lines)

    def create_high_level_plan_display(self, plan_data: Dict[str, Any]):
        """Display the generated high-level plan for teacher review"""
        return Div(
            Card(
                Header(
                    H3("📋 High-Level Lesson Plan", cls="text-success", style="color: white;"),
                    P("Please review the plan below and provide feedback if needed", style="color: #e5e7eb;"),
                    cls="pb-3",
                    style="background-color: #1e3a8a; padding: 1rem; margin: -1rem -1rem 1rem -1rem; border-radius: 6px 6px 0 0;"
                ),
                
                # Display the plan content
                Div(
                    NotStr(self._format_lesson_plan_content(plan_data['high_level_plan'])), 
                    cls="plan-content",
                    style="background-color: #1e3a8a !important; color: white !important; padding: 1rem; border-radius: 6px;"
                ),
                
                # Reasoning display (if available)
                Details(
                    Summary("🧠 AI Reasoning Process", cls="cursor-pointer", style="color: white; background-color: #1e3a8a; padding: 0.5rem; border-radius: 6px;"),
                    Div(
                        plan_data.get('plan_reasoning_summary', 'No reasoning available'),
                        cls="p-3 mt-2 border rounded",
                        style="background-color: #1e3a8a; color: white; border-color: #1e3a8a;"
                    ),
                    cls="mb-4",
                    style="background-color: #1e3a8a; border-radius: 6px;"
                ) if plan_data.get('plan_reasoning_summary') else None,
                
                # Teacher feedback form
                Form(
                    Div(
                        Label("Teacher Feedback & Modifications:", cls="font-weight-bold", style="color: black;"),
                        P("Provide additional instructions or request changes to the plan:", 
                          cls="text-muted small", style="color: black;"),
                        Textarea(
                            name="teacher_feedback",
                            placeholder="e.g., 'Focus more on hands-on activities', 'Add assessment opportunities', 'Modify Section 2 approach'...",
                            rows=4,
                            cls="w-full"
                        ),
                        cls="mb-3"
                    ),
                    
                    # Hidden fields to pass plan data
                    Input(type="hidden", name="plan_data", value=json.dumps(plan_data)),
                    
                    Grid(
                        Button(
                            "🔄 Regenerate Plan",
                            type="submit",
                            name="action",
                            value="regenerate",
                            hx_post="/api/lesson/process-feedback",
                            hx_target="#lesson-content",
                            hx_swap="innerHTML",
                            hx_indicator="#loading-indicator",
                            cls="btn-warning"
                        ),
                        Button(
                            "✅ Approve & Continue",
                            type="submit",
                            name="action",
                            value="approve",
                            hx_post="/api/lesson/process-feedback",
                            hx_target="#lesson-content",
                            hx_swap="innerHTML",
                            hx_indicator="#loading-indicator",
                            cls="btn-success"
                        ),
                        cls="grid-cols-2 gap-3"
                    )
                ),
                
                cls="p-4",
                style="background-color: #1e3a8a;"
            ),
            
            Style("""
                .plan-content {
                    white-space: pre-wrap;
                    line-height: 1.6;
                    font-size: 0.95rem;
                    color: white !important;
                    background-color: #1e3a8a !important;
                }
                .p-3.mb-4.border.rounded {
                    background-color: #1e3a8a !important;
                }
                .btn-warning {
                    background: #ffc107;
                    border: none;
                    color: #212529;
                    padding: 0.75rem 1.5rem;
                    border-radius: 6px;
                    font-weight: 500;
                }
                .btn-success {
                    background: #28a745;
                    border: none;
                    color: white;
                    padding: 0.75rem 1.5rem;
                    border-radius: 6px;
                    font-weight: 500;
                }
                .bg-info-light {
                    background-color: #e3f2fd;
                }
                summary {
                    font-weight: 600;
                    padding: 0.5rem;
                }
            """)
        )

    def create_final_lesson_display(self, lesson_data: Dict[str, Any]):
        """Display the complete lesson plan in a beautiful format similar to the HTML viewer"""
        structured_activities = lesson_data.get('structured_activities', {})
        
        return Div(
            Card(
                Header(
                    H2("📚 Complete Lesson Plan", cls="text-center text-success"),
                    P("Your comprehensive lesson plan is ready!", cls="text-center text-muted"),
                    cls="pb-4"
                ),
                
                # Lesson Metadata
                self._create_metadata_section(lesson_data.get('lesson_metadata', {})),
                
                # High-Level Plan Summary
                self._create_plan_summary_section(lesson_data),
                
                # SLS Tools and KAT
                self._create_tools_and_kat_section(structured_activities),
                
                # Activities by Section
                self._create_activities_section(structured_activities),
                
                # Download and Actions
                Div(
                    Grid(
                        Button(
                            "📥 Download JSON",
                            hx_post="/api/lesson/download",
                            hx_vals=json.dumps({"lesson_data": lesson_data}),
                            cls="btn-info"
                        ),
                        Button(
                            "🔄 Generate New Lesson",
                            hx_get="/lesson-generator",
                            hx_target="#lesson-content",
                            hx_swap="innerHTML",
                            cls="btn-primary"
                        ),
                        cls="grid-cols-2 gap-3"
                    ),
                    cls="mt-4 p-3 border-top"
                ),
                
                cls="p-4"
            ),
            
            self._create_lesson_display_styles()
        )
    
    def _create_metadata_section(self, metadata: Dict[str, Any]):
        """Create the metadata display section"""
        return Div(
            H3("📋 Lesson Information", cls="section-header"),
            Grid(
                *[
                    Div(
                        Div(label, cls="metadata-label"),
                        Div(str(value), cls="metadata-value"),
                        cls="metadata-item"
                    )
                    for label, value in [
                        ("Title", metadata.get('title', 'N/A')),
                        ("Subject", metadata.get('subject', 'N/A')),
                        ("Topic", metadata.get('topic', 'N/A')),
                        ("Level/Grade", metadata.get('level_grade', 'N/A')),
                        ("Sections", metadata.get('lesson_structure', {}).get('num_sections', 'N/A')),
                        ("Activities per Section", metadata.get('lesson_structure', {}).get('max_activities_per_section', 'N/A')),
                        ("Generated", metadata.get('generation_timestamp', 'N/A')),
                        ("Additional Instructions", metadata.get('additional_instructions', 'None'))
                    ]
                ],
                cls="grid-cols-2 gap-3 mb-4"
            ),
            cls="metadata-section"
        )
    
    def _create_plan_summary_section(self, lesson_data: Dict[str, Any]):
        """Create the high-level plan summary section"""
        generation_process = lesson_data.get('generation_process', {})
        plan_data = generation_process.get('step_1_high_level_plan', {})
        
        if not plan_data:
            return None
        
        return Div(
            H3("🎯 High-Level Plan Summary", cls="section-header"),
            Div(
                NotStr(self._format_lesson_plan_content(plan_data.get('generated_content', ''))),
                cls="plan-summary-content"
            ),
            
            # Teacher feedback if any
            Div(
                H4("👨‍🏫 Teacher Feedback", cls="text-info"),
                Div(
                    plan_data.get('teacher_feedback', 'No modifications requested'),
                    cls="teacher-feedback-content"
                ),
                cls="mt-3"
            ) if plan_data.get('teacher_feedback') and plan_data.get('teacher_feedback') != 'No additional modifications requested.' else None,
            
            cls="plan-summary-section mb-4"
        )
    
    def _create_tools_and_kat_section(self, structured_activities: Dict[str, Any]):
        """Create the SLS tools and KAT recommendations section"""
        if not structured_activities:
            return None
        
        return Div(
            # SLS Tools
            Div(
                H3("🛠️ Selected SLS Tools", cls="section-header"),
                Div(
                    *[
                        Div(tool, cls="tool-item")
                        for tool in structured_activities.get('selected_sls_tools', [])
                    ],
                    cls="tools-container"
                ),
                cls="mb-4"
            ) if structured_activities.get('selected_sls_tools') else None,
            
            # KAT Recommendations
            Div(
                H3("🎯 Key Applications of Technology (KAT)", cls="section-header"),
                Div(
                    *[
                        Div(kat, cls="kat-item")
                        for kat in structured_activities.get('recommended_kat', [])
                    ],
                    cls="kat-container"
                ),
                cls="mb-4"
            ) if structured_activities.get('recommended_kat') else None,
            
            cls="tools-kat-section"
        )
    
    def _create_activities_section(self, structured_activities: Dict[str, Any]):
        """Create the activities display section"""
        activities = structured_activities.get('activities', [])
        if not activities:
            return None
        
        # Group activities by section
        sections_dict = {}
        for activity in activities:
            section = activity.get('section', 'Section 1')
            if section not in sections_dict:
                sections_dict[section] = []
            sections_dict[section].append(activity)
        
        return Div(
            H3("📋 Lesson Activities by Section", cls="section-header"),
            *[
                Div(
                    Div(
                        H4(f"📝 {section_name}", cls="section-title"),
                        Span(f"{len(section_activities)} Activities", cls="activity-count"),
                        cls="section-header-row"
                    ),
                    
                    # Activities table
                    Table(
                        Thead(
                            Tr(
                                Th("Interaction", cls="col-interaction"),
                                Th("Duration", cls="col-duration"),
                                Th("Activity Details", cls="col-details"),
                                Th("SLS Tools & Analysis", cls="col-tools")
                            )
                        ),
                        Tbody(
                            *[
                                Tr(
                                    Td(
                                        Span(
                                            activity.get('interaction_type', 'N/A'),
                                            cls=f"interaction-badge {self._get_interaction_class(activity.get('interaction_type', ''))}"
                                        )
                                    ),
                                    Td(
                                        Span(
                                            activity.get('duration', 'N/A'),
                                            cls="duration-badge"
                                        )
                                    ),
                                    Td(
                                        self._format_activity_details(activity),
                                        cls="activity-details-cell"
                                    ),
                                    Td(
                                        self._format_sls_tools(activity),
                                        cls="sls-tools-cell"
                                    )
                                )
                                for activity in section_activities
                            ]
                        ),
                        cls="activities-table"
                    ),
                    cls="section-container mb-4"
                )
                for section_name, section_activities in sections_dict.items()
            ],
            cls="activities-section"
        )
    
    def _get_interaction_class(self, interaction_type: str) -> str:
        """Get CSS class for interaction type badge"""
        interaction_lower = interaction_type.lower().replace(' ', '-').replace('/', '-')
        return interaction_lower
    
    def _format_activity_details(self, activity: Dict[str, Any]) -> Div:
        """Format activity details for display"""
        return Div(
            # Activity title
            Div(activity.get('title', 'Activity'), cls="activity-title"),
            
            # Learning objectives
            Div(
                Strong("Learning Objectives:"),
                Ul(
                    *[Li(obj) for obj in activity.get('learning_objectives', [])],
                    cls="objectives-list"
                ),
                cls="activity-section"
            ) if activity.get('learning_objectives') else None,
            
            # Instructions
            Div(
                Strong("Instructions:"),
                Div(
                    activity.get('instructions', '').replace('\n', '<br>'),
                    cls="instructions-content"
                ),
                cls="activity-section"
            ) if activity.get('instructions') else None,
            
            # KAT Alignment
            Div(
                Strong("KAT Alignment:"),
                Div(
                    self._highlight_kat_terms(activity.get('kat_alignment', '')),
                    cls="kat-content"
                ),
                cls="activity-section"
            ) if activity.get('kat_alignment') else None,
            
            cls="activity-details"
        )
    
    def _format_sls_tools(self, activity: Dict[str, Any]) -> Div:
        """Format SLS tools and data analysis for display"""
        return Div(
            # SLS Tools
            Div(
                Strong("SLS Tools:"),
                Div(
                    activity.get('sls_tools', '').replace('\n', '<br>'),
                    cls="sls-tools-content"
                ),
                cls="sls-tools-section"
            ) if activity.get('sls_tools') else None,
            
            # Data Analysis
            Div(
                Strong("📊 Data Analysis:"),
                Div(
                    activity.get('data_analysis', '').replace('\n', '<br>'),
                    cls="data-analysis-content"
                ),
                cls="data-analysis-section"
            ) if activity.get('data_analysis') else None,
            
            cls="sls-tools-container"
        )
    
    def _highlight_kat_terms(self, text: str) -> str:
        """Highlight KAT terms in the text"""
        kat_terms = [
            "Embed scaffolding", "Facilitate learning together", "Foster conceptual change",
            "Support assessment for learning", "Develop metacognition", "Provide differentiation",
            "Enable personalization", "Increase motivation"
        ]
        
        highlighted_text = text
        for term in kat_terms:
            highlighted_text = highlighted_text.replace(
                term,
                f'<span class="kat-highlight">{term}</span>'
            )
        
        return highlighted_text.replace('\n', '<br>')
    
    def _create_lesson_display_styles(self):
        """Create CSS styles for the lesson display"""
        return Style("""
            .section-header {
                color: #667eea;
                border-bottom: 2px solid #667eea;
                padding-bottom: 0.5rem;
                margin-bottom: 1rem;
            }
            .metadata-section {
                background: #1e3a8a;
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1.5rem;
                border-left: 4px solid #667eea;
            }
            .metadata-item {
                background: #991b1b;
                padding: 0.75rem;
                border-radius: 6px;
                border: 1px solid #e9ecef;
            }
            .metadata-label {
                font-weight: bold;
                color: #fbbf24;
                font-size: 0.9rem;
            }
            .metadata-value {
                margin-top: 0.25rem;
                color: white;
            }
            .plan-summary-section {
                background: #1e3a8a;
                border-radius: 8px;
                padding: 1rem;
                border-left: 4px solid #2196f3;
            }
            .plan-summary-content {
                line-height: 1.6;
                white-space: pre-wrap;
                color: white;
            }
            .teacher-feedback-content {
                background: #fff3cd;
                padding: 0.75rem;
                border-radius: 6px;
                border-left: 3px solid #ffc107;
                font-style: italic;
            }
            .tools-container, .kat-container {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
            }
            .tool-item, .kat-item {
                background: #991b1b;
                color: white;
                padding: 0.5rem 0.75rem;
                border-radius: 4px;
                font-size: 0.9rem;
            }
            .section-container {
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .section-header-row {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .section-title {
                margin: 0;
                font-size: 1.1rem;
            }
            .activity-count {
                background: rgba(255,255,255,0.2);
                padding: 0.25rem 0.5rem;
                border-radius: 12px;
                font-size: 0.85rem;
            }
            .activities-table {
                width: 100%;
                border-collapse: collapse;
            }
            .activities-table th {
                background: #f8f9fa;
                padding: 0.75rem 0.5rem;
                text-align: left;
                font-weight: 600;
                color: #495057;
                border-bottom: 2px solid #dee2e6;
            }
            .activities-table td {
                padding: 1rem 0.5rem;
                border-bottom: 1px solid #dee2e6;
                vertical-align: top;
            }
            .activities-table tr:hover {
                background-color: #f8f9fa;
            }
            .interaction-badge {
                padding: 0.25rem 0.75rem;
                border-radius: 12px;
                font-size: 0.85rem;
                font-weight: 500;
                white-space: nowrap;
            }
            .student-student { background: #1e3a8a; color: white; }
            .teacher-student { background: #1e3a8a; color: white; }
            .student-community { background: #1e3a8a; color: white; }
            .student-content { background: #1e3a8a; color: white; }
            .duration-badge {
                background: #667eea;
                color: white;
                padding: 0.4rem 0.75rem;
                border-radius: 12px;
                font-size: 0.85rem;
                font-weight: 500;
                white-space: nowrap;
            }
            .activity-details {
                line-height: 1.5;
            }
            .activity-title {
                color: #667eea;
                font-weight: bold;
                font-size: 1rem;
                margin-bottom: 0.75rem;
            }
            .activity-section {
                margin-bottom: 0.75rem;
            }
            .objectives-list {
                margin: 0.5rem 0 0 1rem;
                padding-left: 0;
            }
            .instructions-content, .kat-content {
                margin-top: 0.5rem;
                line-height: 1.5;
            }
            .kat-highlight {
                background: linear-gradient(120deg, #f093fb 0%, #f5576c 100%);
                color: white;
                padding: 2px 6px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 0.9rem;
            }
            .sls-tools-section {
                background: #1e3a8a;
                color: white;
                padding: 0.75rem;
                border-radius: 6px;
                border-left: 3px solid #28a745;
                margin-bottom: 0.75rem;
            }
            .data-analysis-section {
                background: #1e3a8a;
                color: white;
                padding: 0.75rem;
                border-radius: 6px;
                border-left: 3px solid #ffc107;
            }
            .sls-tools-content, .data-analysis-content {
                margin-top: 0.5rem;
                line-height: 1.5;
            }
            .col-interaction { width: 12%; }
            .col-duration { width: 10%; }
            .col-details { width: 50%; }
            .col-tools { width: 28%; }
            .btn-info {
                background: #17a2b8;
                border: none;
                color: white;
                padding: 0.75rem 1.5rem;
                border-radius: 6px;
                font-weight: 500;
            }
        """)

# API Functions for Lesson Generation
async def generate_high_level_plan_api(self, lesson_details: Dict[str, str], use_reasoning: bool = True) -> Dict[str, Any]:
    """Generate a high-level lesson plan using the selected model"""
    try:
        model = self.reasoning_model if use_reasoning else self.non_reasoning_model
        
        prompt = f"""
        <Role>As an experienced education coach in Singapore proficient in e-Pedagogy, your role is to create a high-level lesson plan outline that references the e-pedagogy framework and active learning principles. Focus on strategic planning using the KAT framework.</Role>

        <Context>You are creating a strategic overview of a lesson before detailed planning. This high-level plan will help teachers understand the overall approach and make modifications before detailed activity generation.</Context>

        Using the following information:

        Module title: {lesson_details['lesson_title']}
        Subject: {lesson_details['subject']}
        Topic: {lesson_details['topic']}
        Level/Grade: {lesson_details['level_grade']}
        Number of sections: {lesson_details['num_sections']}
        Number of activities per section: {lesson_details['max_activities']}
        Additional Instructions: {lesson_details['additional_instructions']}

        Create a high-level lesson plan outline that focuses on strategic pedagogical decisions.

        Your output should only be rich text, do not include hyperlinks, code snippets, mathematical formulas or xml.

        Structure your response as follows:

        **LESSON OVERVIEW:**
        [Provide a comprehensive lesson overview of 3-4 sentences describing the main learning journey]

        **RECOMMENDED KEY APPLICATIONS OF TECHNOLOGY (KAT):**
        Select exactly 2 KAT from this list that are most relevant: Foster conceptual change; Support assessment for learning; Facilitate learning together; Develop metacognition; Provide differentiation; Embed scaffolding; Enable personalization; Increase motivation.

        1. [First KAT] - [Detailed explanation of why this KAT is essential for this topic and how it will be implemented]
        2. [Second KAT] - [Detailed explanation of why this KAT is essential for this topic and how it will be implemented]

        **PEDAGOGICAL APPROACH:**
        [Describe the overall pedagogical strategy, interaction patterns, and learning progression]

        **HIGH-LEVEL SECTION BREAKDOWN:**
        
        Section 1: [Title and Purpose]
        - Main Learning Focus: [What students will learn]
        - Pedagogical Strategy: [How learning will be facilitated]
        - KAT Implementation: [How the selected KAT will be applied]
        
        Section 2: [Title and Purpose]
        - Main Learning Focus: [What students will learn]
        - Pedagogical Strategy: [How learning will be facilitated]
        - KAT Implementation: [How the selected KAT will be applied]

        [Continue for all {lesson_details['num_sections']} sections]

        **ASSESSMENT STRATEGY:**
        [Describe how student learning will be monitored and assessed throughout the lesson]

        **POTENTIAL SLS TOOLS RECOMMENDATION:**
        [Suggest 3-4 SLS tools that align with the pedagogical approach and KAT implementation]
        """
        
        if use_reasoning:
            response = self.openai_client.responses.create(
                model=model,
                input=prompt,
                reasoning={"effort": "medium", "summary": "auto"},
                max_output_tokens=16000,
            )
            
            reasoning_items = [item for item in response.output if item.type == 'reasoning']
            reasoning_summary = reasoning_items[0].summary[0].text if reasoning_items and reasoning_items[0].summary else f"Internal reasoning by {model} model"
            output_text = response.output_text
        else:
            response = self.openai_client.responses.create(
                model=model,
                input=[{"role": "user", "content": prompt}],
                max_output_tokens=16000,
            )
            
            reasoning_summary = f"No reasoning - using {model} model"
            if hasattr(response, 'output_text'):
                output_text = response.output_text
            elif hasattr(response, 'output') and response.output:
                if isinstance(response.output, list) and len(response.output) > 0:
                    output_text = response.output[0].text
                else:
                    output_text = str(response.output)
            else:
                output_text = str(response)
        
        return {
            "lesson_details": lesson_details,
            "high_level_plan": output_text,
            "plan_reasoning_summary": reasoning_summary,
            "model_used": model,
            "use_reasoning": use_reasoning
        }
        
    except Exception as e:
        return {"error": f"Failed to generate high-level plan: {str(e)}"}

async def generate_sections_and_activities_api(self, plan_data: Dict[str, Any], teacher_feedback: str = "") -> Dict[str, Any]:
    """Generate sections and activities based on the approved plan"""
    try:
        lesson_details = plan_data['lesson_details']
        high_level_plan = plan_data['high_level_plan']
        use_reasoning = plan_data.get('use_reasoning', True)
        model = self.reasoning_model if use_reasoning else self.non_reasoning_model
        
        # Convert string values to integers
        num_sections = int(lesson_details['num_sections'])
        max_activities = int(lesson_details['max_activities'])
        total_activities = num_sections * max_activities
        
        # First generate sections
        sections_prompt = f"""
        <Role>As an experienced education coach in Singapore proficient in e-Pedagogy, your role is to create detailed lesson sections that implement the approved high-level plan and incorporate teacher feedback.</Role>

        <Context>You are now creating detailed lesson sections based on a previously approved high-level plan. The sections should implement the pedagogical strategies and KAT framework outlined in the plan.</Context>

        Using the following information:

        Module title: {lesson_details['lesson_title']}
        Subject: {lesson_details['subject']}
        Topic: {lesson_details['topic']}
        Level/Grade: {lesson_details['level_grade']}
        Number of sections: {num_sections}
        Number of activities per section: {max_activities}
        Additional Instructions: {lesson_details['additional_instructions']}
        
        IMPORTANT: Base your detailed sections on this approved high-level plan:
        
        {high_level_plan}
        
        Teacher's additional feedback/modifications:
        {teacher_feedback}
        
        Ensure your detailed sections align with the pedagogical approach and KAT implementation outlined in the high-level plan above.

        Create detailed lesson sections that implement the high-level plan. 

        IMPORTANT: You must create EXACTLY {num_sections} sections, and each section will later have EXACTLY {max_activities} activities.

        Your output should only be rich text, do not include hyperlinks, code snippets, mathematical formulas or xml.

        Structure your response as follows:

        **LESSON DESCRIPTION:**
        [Provide a lesson description of maximum 5 sentences that describes the lesson to the student]

        **CONFIRMED KEY APPLICATIONS OF TECHNOLOGY (KAT):**
        [List the 2 KAT from the high-level plan and confirm their implementation]

        **DETAILED LESSON SECTIONS:**

        Section 1: [Title]
        - Learning Objectives: [List specific learning objectives for this section]
        - Description: [Detailed description implementing the high-level plan]
        - Pedagogical Approach: [Specific teaching strategies to be used]
        - Teacher Notes: [Implementation guidance for teachers]
        - KAT Connection: [How this section implements the selected Key Applications of Technology]

        Section 2: [Title]
        - Learning Objectives: [List specific learning objectives for this section]
        - Description: [Detailed description implementing the high-level plan]
        - Pedagogical Approach: [Specific teaching strategies to be used]
        - Teacher Notes: [Implementation guidance for teachers]
        - KAT Connection: [How this section implements the selected Key Applications of Technology]

        [Continue for all {num_sections} sections]
        """
        
        # Generate sections
        if use_reasoning:
            sections_response = self.openai_client.responses.create(
                model=model,
                input=sections_prompt,
                reasoning={"effort": "medium", "summary": "auto"},
                max_output_tokens=16000,
            )
            
            reasoning_items = [item for item in sections_response.output if item.type == 'reasoning']
            sections_reasoning = reasoning_items[0].summary[0].text if reasoning_items and reasoning_items[0].summary else f"Internal reasoning by {model} model"
            sections_text = sections_response.output_text
        else:
            sections_response = self.openai_client.responses.create(
                model=model,
                input=[{"role": "user", "content": sections_prompt}],
                max_output_tokens=16000,
            )
            
            sections_reasoning = f"No reasoning - using {model} model"
            if hasattr(sections_response, 'output_text'):
                sections_text = sections_response.output_text
            elif hasattr(sections_response, 'output') and sections_response.output:
                if isinstance(sections_response.output, list) and len(sections_response.output) > 0:
                    sections_text = sections_response.output[0].text
                else:
                    sections_text = str(sections_response.output)
            else:
                sections_text = str(sections_response)
        
        # Now generate activities
        activities_prompt = f"""
        <Role>As an experienced education coach in Singapore proficient in e-Pedagogy, your role is to create detailed activities that implement the approved high-level plan and detailed sections.</Role>

        <Context>You are creating specific learning activities that implement the pedagogical strategies from the approved high-level plan and align with the detailed lesson sections.</Context>

        Based on the following approved lesson sections:
        
        {sections_text}
        
        IMPORTANT: Base your activities on this approved high-level plan and teacher feedback:
        
        HIGH-LEVEL PLAN:
        {high_level_plan}
        
        TEACHER FEEDBACK:
        {teacher_feedback}
        
        Ensure your activities implement the pedagogical strategies outlined in the plan.
        
        Using the following information:
        Module title: {lesson_details['lesson_title']}
        Subject: {lesson_details['subject']}
        Topic: {lesson_details['topic']}
        Level/Grade: {lesson_details['level_grade']}
        Number of sections: {num_sections}
        Number of activities per section: {max_activities}
        Additional Instructions: {lesson_details['additional_instructions']}

        CRITICAL REQUIREMENTS:
        1. You must create EXACTLY {max_activities} activities for EACH of the {num_sections} sections
        2. Total activities = {num_sections} sections × {max_activities} activities = {total_activities} activities
        3. Each activity must be clearly numbered (Activity 1, Activity 2, etc.)
        4. Activities must implement the pedagogical approach from the high-level plan

        First, select NOT MORE than 4 unique SLS tools from this list for the overall lesson: Text/Media, Progressive Quiz, Auto-graded Quiz, Teacher-marked Quiz, Multiple-Choice/ Multiple-Response Question, Fill-in-the-blank Question, Click and Drop Question, Error Editing Question, Free Response Question, Audio Response Question, Rubrics, Tooltip, Interactive Thinking Tool, Poll, Discussion Board, Team Activities, Subgroups, Add Section Prerequisites, Set Differentiated Access, Gamification - Create Game Stories and Achievements, Gamification - Create Game Teams, Set Optional Activities and Quizzes, Speech Evaluation, Chinese Language E-Dictionary, Embed Canva, Embed Nearpod, Embed Coggle, Embed Genial.ly, Embed Quizizz, Embed Kahoot, Embed Google Docs, Embed Google Sheets, Embed Mentimeter, Embed YouTube Videos, Embed Padlet, Embed Gapminder, Embed GeoGebra, Feedback Assistant Mathematics (FA-Math), Speech Evaluation, Text-to-Speech, Embed Book Creator, Embed Simulations, Adaptive Learning System (ALS), Embed ArcGIS Storymap, Embed ArcGIS Digital Maps, Embed PhET Simulations, Embed Open Source Physics @ Singapore Simulations, Embed CK12 Simulations, Embed Desmos, Short Answer Feedback Assistant (ShortAnsFA), Gamification - Quiz leaderboard and ranking, Gamification - Create branches in game stories, Monitor Assignment Page, Insert Transcript for Video & Audio, Insert Student Tooltip, Add Notes to Audio or Video, Data Assistant, Annotated Feedback Assistant (AFA), Learning Assistant (LEA), SLS Digital Badges.

        Your output should only be rich text, do not include hyperlinks, code snippets, mathematical formulas or xml.

        Please structure your response in the following format:

        **SELECTED SLS TOOLS FOR THIS LESSON:**
        [List the 4 selected SLS tools and briefly explain why each was chosen based on the high-level plan]

        **CONFIRMED KEY APPLICATIONS OF TECHNOLOGY (KAT):**
        [List the 2 KAT from the high-level plan and explain their implementation across activities]

        **LESSON PLAN ACTIVITIES:**

        For each activity, provide the following information in this exact format:

        Activity [Number]: [Activity Title]
        Section: [Which section this belongs to]
        Interaction Type: [Student-Student/Teacher-Student/Student-Community/Student-Content]
        Duration: [X minutes]
        Learning Objectives:
        • [Objective 1]
        • [Objective 2]

        Instructions:
        [Detailed step-by-step instructions for students implementing the pedagogical approach]

        KAT Alignment:
        [How this activity implements the selected Key Applications of Technology from the plan]

        SLS Tools:
        [List of specific SLS tools used in this activity]

        Data Analysis:
        [Monitoring tools and methods for tracking learning progress]

        Teaching Notes:
        [Implementation guidance for teachers based on the approved pedagogical approach]

        ---

        IMPORTANT: 
        - You must create exactly {total_activities} activities total
        - Number activities sequentially (Activity 1, Activity 2, Activity 3, etc.)
        - Each activity must specify which section it belongs to
        - Include all required components for each activity
        - Ensure activities implement the pedagogical strategies from the high-level plan
        """
        
        # Generate activities
        if use_reasoning:
            activities_response = self.openai_client.responses.create(
                model=model,
                input=activities_prompt,
                reasoning={"effort": "medium", "summary": "auto"},
                max_output_tokens=16000,
            )
            
            reasoning_items = [item for item in activities_response.output if item.type == 'reasoning']
            activities_reasoning = reasoning_items[0].summary[0].text if reasoning_items and reasoning_items[0].summary else f"Internal reasoning by {model} model"
            activities_text = activities_response.output_text
        else:
            activities_response = self.openai_client.responses.create(
                model=model,
                input=[{"role": "user", "content": activities_prompt}],
                max_output_tokens=16000,
            )
            
            activities_reasoning = f"No reasoning - using {model} model"
            if hasattr(activities_response, 'output_text'):
                activities_text = activities_response.output_text
            elif hasattr(activities_response, 'output') and activities_response.output:
                if isinstance(activities_response.output, list) and len(activities_response.output) > 0:
                    activities_text = activities_response.output[0].text
                else:
                    activities_text = str(activities_response.output)
            else:
                activities_text = str(activities_response)
        
        # Parse activities into structured format
        structured_activities = self.parse_activities_to_json(activities_text, lesson_details)
        
        # Create final lesson data structure
        final_lesson_data = {
            "lesson_metadata": {
                "title": lesson_details['lesson_title'],
                "subject": lesson_details['subject'],
                "topic": lesson_details['topic'],
                "level_grade": lesson_details['level_grade'],
                "additional_instructions": lesson_details['additional_instructions'],
                "lesson_structure": {
                    "num_sections": int(lesson_details['num_sections']),
                    "max_activities_per_section": int(lesson_details['max_activities'])
                },
                "generation_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "models_used": {
                    "plan_model": model,
                    "sections_model": model,
                    "activities_model": model,
                    "reasoning_enabled": use_reasoning
                }
            },
            "generation_process": {
                "step_1_high_level_plan": {
                    "reasoning_summary": plan_data.get('plan_reasoning_summary', ''),
                    "generated_content": high_level_plan,
                    "teacher_feedback": teacher_feedback
                },
                "step_2_sections": {
                    "reasoning_summary": sections_reasoning,
                    "generated_content": sections_text
                },
                "step_3_activities": {
                    "reasoning_summary": activities_reasoning,
                    "generated_content": activities_text,
                    "structured_activities": structured_activities
                }
            },
            "structured_activities": structured_activities,
            "errors": {}
        }
        
        return final_lesson_data
        
    except Exception as e:
        return {"error": f"Failed to generate sections and activities: {str(e)}"}

def parse_activities_to_json(self, content: str, lesson_details: Dict[str, str]) -> Dict[str, Any]:
    """Parse the structured activity response into JSON format"""
    lines = content.split('\n')
    
    structured_data = {
        "selected_sls_tools": [],
        "recommended_kat": [],
        "activities": []
    }
    
    current_activity = {}
    current_section = ""
    
    # Convert max_activities to integer for calculations
    max_activities_per_section = int(lesson_details.get('max_activities', 1))
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Parse SLS Tools
        if "SELECTED SLS TOOLS" in line:
            i += 1
            while i < len(lines):
                line_content = lines[i].strip()
                if "CONFIRMED KEY APPLICATIONS" in line_content or "**CONFIRMED" in line_content:
                    break
                if line_content and not line_content.startswith("**") and not line_content.startswith("["):
                    structured_data["selected_sls_tools"].append(line_content)
                i += 1
            continue
        
        # Parse KAT
        if "CONFIRMED KEY APPLICATIONS" in line or "KEY APPLICATIONS OF TECHNOLOGY" in line:
            i += 1
            while i < len(lines):
                line_content = lines[i].strip()
                if "LESSON PLAN ACTIVITIES" in line_content or "**LESSON PLAN" in line_content:
                    break
                if line_content and not line_content.startswith("**") and not line_content.startswith("["):
                    structured_data["recommended_kat"].append(line_content)
                i += 1
            continue
        
        # Parse Activities - Handle both "Activity X:" and "**Activity X:**" formats
        activity_match = None
        if line.startswith("Activity ") and (":" in line):
            activity_match = line
        elif line.startswith("**Activity ") and (":**" in line or line.endswith("**")):
            activity_match = line.replace("**", "").strip()
        
        if activity_match:
            # Save previous activity if exists
            if current_activity and current_activity.get("title"):
                structured_data["activities"].append(current_activity)
            
            # Start new activity
            current_activity = {
                "title": activity_match,
                "section": "",
                "interaction_type": "",
                "duration": "",
                "learning_objectives": [],
                "instructions": "",
                "kat_alignment": "",
                "sls_tools": "",
                "data_analysis": "",
                "teaching_notes": ""
            }
        
        elif current_activity:
            if line.startswith("Section:"):
                current_activity["section"] = line.replace("Section:", "").strip()
            
            elif line.startswith("Interaction Type:"):
                current_activity["interaction_type"] = line.replace("Interaction Type:", "").strip()
            
            elif line.startswith("Duration:"):
                current_activity["duration"] = line.replace("Duration:", "").strip()
            
            elif line.startswith("Learning Objectives:"):
                i += 1
                while i < len(lines):
                    obj_line = lines[i].strip()
                    if obj_line.startswith("•"):
                        current_activity["learning_objectives"].append(obj_line[1:].strip())
                    elif obj_line and not obj_line.startswith(("Instructions:", "KAT Alignment:", "SLS Tools:", "Data Analysis:", "Teaching Notes:", "Activity ", "---", "**Activity")):
                        if obj_line.startswith("•"):
                            current_activity["learning_objectives"].append(obj_line[1:].strip())
                    else:
                        break
                    i += 1
                continue
            
            elif line.startswith("Instructions:"):
                i += 1
                instructions = []
                while i < len(lines):
                    inst_line = lines[i].strip()
                    if inst_line.startswith(("KAT Alignment:", "SLS Tools:", "Data Analysis:", "Teaching Notes:", "Activity ", "---", "**Activity")):
                        break
                    if inst_line:
                        instructions.append(inst_line)
                    i += 1
                current_activity["instructions"] = "\n".join(instructions)
                continue
            
            elif line.startswith("KAT Alignment:"):
                i += 1
                kat_content = []
                while i < len(lines):
                    kat_line = lines[i].strip()
                    if kat_line.startswith(("SLS Tools:", "Data Analysis:", "Teaching Notes:", "Activity ", "---", "**Activity")):
                        break
                    if kat_line:
                        kat_content.append(kat_line)
                    i += 1
                current_activity["kat_alignment"] = "\n".join(kat_content)
                continue
            
            elif line.startswith("SLS Tools:"):
                i += 1
                sls_content = []
                while i < len(lines):
                    sls_line = lines[i].strip()
                    if sls_line.startswith(("Data Analysis:", "Teaching Notes:", "Activity ", "---", "**Activity")):
                        break
                    if sls_line:
                        sls_content.append(sls_line)
                    i += 1
                current_activity["sls_tools"] = "\n".join(sls_content)
                continue
            
            elif line.startswith("Data Analysis:"):
                i += 1
                data_content = []
                while i < len(lines):
                    data_line = lines[i].strip()
                    if data_line.startswith(("Teaching Notes:", "Activity ", "---", "**Activity")):
                        break
                    if data_line:
                        data_content.append(data_line)
                    i += 1
                current_activity["data_analysis"] = "\n".join(data_content)
                continue
            
            elif line.startswith("Teaching Notes:"):
                i += 1
                notes_content = []
                while i < len(lines):
                    notes_line = lines[i].strip()
                    if notes_line.startswith(("Activity ", "---", "**Activity")) or (notes_line.startswith("**") and "Activity" not in notes_line):
                        break
                    if notes_line:
                        notes_content.append(notes_line)
                    i += 1
                current_activity["teaching_notes"] = "\n".join(notes_content)
                continue
        
        i += 1
    
    # Don't forget the last activity
    if current_activity and current_activity.get("title"):
        structured_data["activities"].append(current_activity)
    
    # Clean up and validate data
    for activity in structured_data["activities"]:
        # Ensure section is properly assigned
        if not activity["section"] and structured_data["activities"]:
            # Try to infer section from activity number
            try:
                activity_num = int(activity["title"].split()[1].rstrip(":"))
                section_num = ((activity_num - 1) // max_activities_per_section) + 1
                activity["section"] = f"Section {section_num}"
            except:
                activity["section"] = "Section 1"
    
    # Sort activities by activity number to ensure proper order
    def extract_activity_number(activity):
        try:
            title = activity.get("title", "")
            import re
            match = re.search(r'Activity\s*(\d+)', title, re.IGNORECASE)
            if match:
                return int(match.group(1))
            return 0
        except:
            return 0
    
    structured_data["activities"].sort(key=extract_activity_number)
    
    return structured_data

# Add the API functions to the class
LessonGeneratorForm.generate_high_level_plan_api = generate_high_level_plan_api
LessonGeneratorForm.generate_sections_and_activities_api = generate_sections_and_activities_api
LessonGeneratorForm.parse_activities_to_json = parse_activities_to_json

# Create global instance
lesson_generator_form = LessonGeneratorForm()
