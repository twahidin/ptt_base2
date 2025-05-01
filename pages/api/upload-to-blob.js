import { put } from '@vercel/blob';
import { NextResponse } from 'next/server';
import formidable from 'formidable';
import { createReadStream } from 'fs';

export const config = {
  api: {
    bodyParser: false,
  },
};

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const form = formidable({});
    const [fields, files] = await form.parse(req);
    
    const file = files.file?.[0];
    const filename = fields.filename?.[0];
    const allowOverwrite = fields.allowOverwrite?.[0] === 'true';
    
    if (!file || !filename) {
      return res.status(400).json({ error: 'File and filename are required' });
    }

    // Upload to Vercel Blob
    const blob = await put(filename, createReadStream(file.filepath), {
      access: 'public',
      allowOverwrite: allowOverwrite,
    });

    return res.status(200).json({ 
      url: blob.url,
      size: blob.size,
      contentType: blob.contentType
    });
  } catch (error) {
    console.error('Error uploading to blob:', error);
    return res.status(500).json({ error: 'Failed to upload to Vercel Blob' });
  }
} 