/**
 * AEGIS — API Proxy Route Handler
 * Forwards all /api/* requests from the browser to the internal backend service.
 * Uses the server-side BACKEND_URL env var (not NEXT_PUBLIC_*) so it works at runtime.
 */

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

async function proxyRequest(request, { params }) {
    const { path } = params;
    const pathname = `/api/${path.join('/')}`;
    const target = new URL(pathname, BACKEND_URL);

    // Forward query parameters
    const requestUrl = new URL(request.url);
    requestUrl.searchParams.forEach((value, key) => target.searchParams.set(key, value));

    // Forward headers, removing hop-by-hop headers
    const headers = new Headers(request.headers);
    headers.delete('host');
    headers.delete('connection');

    const init = {
        method: request.method,
        headers,
    };

    // Forward request body for non-GET/HEAD methods
    if (request.method !== 'GET' && request.method !== 'HEAD') {
        init.body = await request.arrayBuffer();
    }

    const response = await fetch(target.toString(), init);

    // Strip hop-by-hop / encoding headers before returning
    const responseHeaders = new Headers(response.headers);
    responseHeaders.delete('transfer-encoding');
    responseHeaders.delete('content-encoding');

    return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
    });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
