import { NextRequest } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8008';

export async function POST(request: NextRequest) {
  const sessionId = request.nextUrl.searchParams.get('sessionId');
  if (!sessionId) {
    return Response.json({ error: 'Missing sessionId' }, { status: 400 });
  }

  const body = await request.json();
  const token = request.headers.get('Authorization') || request.headers.get('authorization') || '';

  const backendUrl = `${BACKEND_URL}/api/v1/sessions/${sessionId}/chat`;

  const res = await fetch(backendUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: token } : {}),
    },
    body: JSON.stringify(body),
  });

  if (!res.ok || !res.body) {
    const errorText = await res.text().catch(() => 'Stream failed');
    return Response.json(
      { error: errorText, code: res.status },
      { status: res.status }
    );
  }

  const encoder = new TextEncoder();
  const decoder = new TextDecoder();

  const transformStream = new TransformStream({
    transform(chunk, controller) {
      const text = decoder.decode(chunk, { stream: true });
      controller.enqueue(encoder.encode(text));
    },
  });

  const readableStream = res.body.pipeThrough(transformStream);

  return new Response(readableStream, {
    status: 200,
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  });
}
