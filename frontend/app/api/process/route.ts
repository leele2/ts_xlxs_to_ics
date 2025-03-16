// frontend/app/api/process/route.ts
import { NextRequest, NextResponse } from "next/server";
import axios from "axios";
import { del } from "@vercel/blob";

export const maxDuration = 60; // Increase timeout limit


export async function POST(req: NextRequest) {
    try {
        const { fileUrl, name_to_search } = await req.json();
        console.log("Sending to Python API:", { fileUrl, name_to_search });

        if (!fileUrl || !name_to_search) {
            return NextResponse.json(
                { error: "Missing fileUrl or name_to_search" },
                { status: 400 }
            );
        }

        // Call the Python backend to process the file
        const pythonApiResponse = await axios.post(
            `${process.env.PYTHON_API_URL}/api/process`,
            { fileUrl, name_to_search },
            { responseType: "arraybuffer" }
        );

        // Delete the file from Vercel Blob after successful processing
        await del(fileUrl);
        console.log(`Deleted Blob: ${fileUrl}`);

        // Return the ICS file to the client
        return new NextResponse(pythonApiResponse.data, {
            status: 200,
            headers: {
                "Content-Disposition": "attachment; filename=shifts.ics",
                "Content-Type": "text/calendar",
            },
        });
    } catch (error) {
        if (axios.isAxiosError(error) && error.response) {
            console.error(
                "Python API response:",
                error.response.status,
                error.response.data
            );
            return NextResponse.json(
                {
                    error:
                        error.response.data?.detail || "Failed to process file",
                },
                { status: error.response.status }
            );
        }
        console.error("Error calling Python API or deleting Blob:", error);
        return NextResponse.json(
            { error: "Failed to process file" },
            { status: 500 }
        );
    }
}
