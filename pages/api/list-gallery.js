import { list } from '@vercel/blob';

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { cursor, prefix } = req.query;
    
    // Default to listing items in the gallery folder
    const galleryPrefix = prefix || 'gallery/';
    
    // List blobs with the specified prefix
    const blobs = await list({
      cursor: cursor || undefined,
      limit: 1000, // Maximum allowed by Vercel Blob
      prefix: galleryPrefix,
    });

    // Parse metadata files to return organized gallery data
    const galleryItems = [];
    const metadataFiles = blobs.blobs.filter(blob => blob.pathname.endsWith('metadata.json'));
    
    for (const metadata of metadataFiles) {
      try {
        // Fetch the metadata JSON content
        const response = await fetch(metadata.url);
        const data = await response.json();
        
        // Add to gallery items
        galleryItems.push({
          id: metadata.pathname.split('/')[1], // Extract folder name as ID
          ...data
        });
      } catch (err) {
        console.error(`Error parsing metadata from ${metadata.url}:`, err);
      }
    }

    return res.status(200).json({
      items: galleryItems,
      cursor: blobs.cursor,
      hasMore: blobs.hasMore
    });
  } catch (error) {
    console.error('Error listing blobs:', error);
    return res.status(500).json({ error: 'Failed to list gallery items' });
  }
} 