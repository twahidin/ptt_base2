from fasthtml.common import *
from starlette.responses import JSONResponse
import json
import asyncio
from components.acp_edit_form import lesson_generator_form

def routes(router):
    """Set up lesson generator routes"""
    
    @router.get("/lesson-generator")
    def get_lesson_generator():
        """Display the lesson generator form"""
        return Title("Lesson Generator"), lesson_generator_form.create_lesson_input_form()
    
    @router.post("/api/lesson/generate-plan")
    async def generate_plan(req):
        """Generate high-level lesson plan"""
        try:
            form_data = await req.form()
            
            # Extract lesson details
            lesson_details = {
                'lesson_title': form_data.get('lesson_title', ''),
                'subject': form_data.get('subject', ''),
                'topic': form_data.get('topic', ''),
                'level_grade': form_data.get('level_grade', ''),
                'additional_instructions': form_data.get('additional_instructions', ''),
                'num_sections': form_data.get('num_sections', '2'),
                'max_activities': form_data.get('max_activities', '2')
            }
            
            # Check if using reasoning model
            use_reasoning = form_data.get('model_type') == 'reasoning'
            
            # Generate high-level plan
            plan_data = await lesson_generator_form.generate_high_level_plan_api(lesson_details, use_reasoning)
            
            if 'error' in plan_data:
                return Div(
                    Card(
                        H3("❌ Error", cls="text-danger"),
                        P(plan_data['error']),
                        Button(
                            "🔄 Try Again",
                            hx_get="/lesson-generator",
                            hx_target="#lesson-content",
                            hx_swap="innerHTML",
                            cls="btn-warning mt-3"
                        ),
                        cls="p-4"
                    )
                )
            
            # Return the high-level plan display for teacher review
            return lesson_generator_form.create_high_level_plan_display(plan_data)
            
        except Exception as e:
            return Div(
                Card(
                    H3("❌ System Error", cls="text-danger"),
                    P(f"An unexpected error occurred: {str(e)}"),
                    Button(
                        "🔄 Try Again",
                        hx_get="/lesson-generator",
                        hx_target="#lesson-content",
                        hx_swap="innerHTML",
                        cls="btn-warning mt-3"
                    ),
                    cls="p-4"
                )
            )
    
    @router.post("/api/lesson/process-feedback")
    async def process_teacher_feedback(req):
        """Process teacher feedback and either regenerate plan or generate sections/activities"""
        try:
            form_data = await req.form()
            action = form_data.get('action')
            teacher_feedback = form_data.get('teacher_feedback', '').strip()
            plan_data_json = form_data.get('plan_data')
            
            if not plan_data_json:
                raise ValueError("Missing plan data")
            
            plan_data = json.loads(plan_data_json)
            
            if action == 'regenerate':
                # Regenerate high-level plan with teacher feedback
                lesson_details = plan_data['lesson_details']
                
                # Add teacher feedback to additional instructions
                if teacher_feedback:
                    original_instructions = lesson_details.get('additional_instructions', '')
                    lesson_details['additional_instructions'] = f"{original_instructions}\n\nTEACHER FEEDBACK: {teacher_feedback}".strip()
                
                # Generate new high-level plan
                new_plan_data = await lesson_generator_form.generate_high_level_plan_api(
                    lesson_details, 
                    plan_data.get('use_reasoning', True)
                )
                
                if 'error' in new_plan_data:
                    return Div(
                        Card(
                            H3("❌ Error Regenerating Plan", cls="text-danger"),
                            P(new_plan_data['error']),
                            cls="p-4"
                        )
                    )
                
                # Return the new high-level plan for review
                return lesson_generator_form.create_high_level_plan_display(new_plan_data)
                
            elif action == 'approve':
                # Generate sections and activities
                final_lesson_data = await lesson_generator_form.generate_sections_and_activities_api(
                    plan_data, 
                    teacher_feedback or "No additional modifications requested."
                )
                
                if 'error' in final_lesson_data:
                    return Div(
                        Card(
                            H3("❌ Error Generating Lesson", cls="text-danger"),
                            P(final_lesson_data['error']),
                            cls="p-4"
                        )
                    )
                
                # Display the complete lesson plan
                return lesson_generator_form.create_final_lesson_display(final_lesson_data)
            
            else:
                raise ValueError("Invalid action")
                
        except Exception as e:
            return Div(
                Card(
                    H3("❌ Processing Error", cls="text-danger"),
                    P(f"Error processing request: {str(e)}"),
                    Button(
                        "🔄 Start Over",
                        hx_get="/lesson-generator",
                        hx_target="#lesson-content",
                        hx_swap="innerHTML",
                        cls="btn-warning mt-3"
                    ),
                    cls="p-4"
                )
            )
    
    @router.post("/api/lesson/download")
    async def download_lesson(req):
        """Download lesson plan as JSON file"""
        try:
            form_data = await req.form()
            lesson_data_str = form_data.get('lesson_data')
            
            if not lesson_data_str:
                return JSONResponse({"error": "No lesson data provided"}, status_code=400)
            
            # Parse the lesson data
            lesson_data = json.loads(lesson_data_str)
            
            # Create filename based on lesson title and timestamp
            title = lesson_data.get('lesson_metadata', {}).get('title', 'lesson_plan')
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')
            
            timestamp = lesson_data.get('lesson_metadata', {}).get('generation_timestamp', 'unknown')
            filename = f"{safe_title}_{timestamp.replace(':', '-').replace(' ', '_')}.json"
            
            # Return JSON file download
            response = JSONResponse(lesson_data)
            response.headers["Content-Disposition"] = f"attachment; filename={filename}"
            response.headers["Content-Type"] = "application/json"
            
            return response
            
        except Exception as e:
            return JSONResponse({"error": f"Download failed: {str(e)}"}, status_code=500)
    
    @router.get("/api/lesson/reset")
    def reset_lesson_generator():
        """Reset the lesson generator form"""
        return lesson_generator_form.create_lesson_input_form()
