import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(req: Request) {
  try {
    const body = await req.json();

    // Call Python FastAPI backend
    const res = await axios.post("http://localhost:8000/analyze", body);
    
    return NextResponse.json(res.data);
  } catch (error: any) {
    console.error(error);
    return NextResponse.json({ error: "Error calling backend" }, { status: 500 });
  }
}
