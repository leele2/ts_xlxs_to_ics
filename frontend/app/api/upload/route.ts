// pages/api/upload.ts (or app/api/upload/route.ts)
import { handleUpload, type HandleUploadBody } from "@vercel/blob/client";
import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
    try {
        const body = (await request.json()) as HandleUploadBody;

        
        const jsonResponse = await handleUpload({
            body,
            request,
            onBeforeGenerateToken: async () => {
                // Here you can add authentication/authorization logic
                // For example, check if user is authenticated
                // if (!user) throw new Error('Unauthorized');

                return {
                    allowedContentTypes: [
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", // .xlsx files
                    ],
                    tokenPayload: JSON.stringify({
                        // You can add custom data here that will be available in onUploadCompleted
                        // For example: userId, custom metadata, etc.
                    }),
                };
            },
            onUploadCompleted: async ({ blob, tokenPayload }) => {
                try {
                    console.log("Upload completed:", blob, tokenPayload);
                    // Here you can add logic to handle the uploaded file
                    // For example, store the blob URL in your database
                } catch (error) {
                    throw new Error("Failed to process uploaded file");
                }
            },
        });

        return NextResponse.json(jsonResponse);
    } catch (error) {
        return NextResponse.json(
            { error: (error as Error).message },
            { status: 400 }
        );
    }
}
