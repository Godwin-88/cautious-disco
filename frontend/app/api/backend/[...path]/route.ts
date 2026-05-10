import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8080";

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}

async function proxy(req: NextRequest, method: string, pathSegments: string[]) {
  const pathSuffix = pathSegments.join("/");
  const target = new URL(`/api/v1/${pathSuffix}`, BACKEND_URL);
  target.search = req.nextUrl.search;

  const body = method !== "GET" && method !== "DELETE" ? await req.arrayBuffer() : undefined;

  const resp = await fetch(target.toString(), {
    method,
    headers: {
      ...Object.fromEntries(req.headers.entries()),
      host: target.host,
    },
    body: body || undefined,
    redirect: "manual",
  });

  const responseHeaders = new Headers();
  for (const [key, value] of resp.headers.entries()) {
    if (!["transfer-encoding", "content-encoding", "content-length", "connection", "keep-alive"].includes(key.toLowerCase())) {
      responseHeaders.set(key, value);
    }
  }
  responseHeaders.set("Access-Control-Allow-Origin", "*");

  return new NextResponse(resp.body, {
    status: resp.status,
    headers: responseHeaders,
  });
}

export async function GET(req: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxy(req, "GET", path);
}

export async function POST(req: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxy(req, "POST", path);
}

export async function PUT(req: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxy(req, "PUT", path);
}

export async function PATCH(req: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxy(req, "PATCH", path);
}

export async function DELETE(req: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxy(req, "DELETE", path);
}
