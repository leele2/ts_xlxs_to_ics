// frontend/app/components/ShiftCalendarUploader.tsx
"use client";

import { useState } from "react";
import axios from "axios";
import { upload } from "@vercel/blob/client";

export default function ShiftCalendarUploader() {
    const [uploadStatus, setUploadStatus] = useState<string>("");

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setUploadStatus("Uploading...");

        try {
            const formData = new FormData(event.currentTarget);
            const file = formData.get("excel_file") as File;
            const name = formData.get("name_to_search") as string;

            if (!file) {
                throw new Error("No file selected");
            }

            // Upload file to Vercel Blob
            const response = await upload(file.name, file, {
                access: "public",
                handleUploadUrl: "/api/upload",
            });

            setUploadStatus("Upload successful!");

            // Call the internal Next.js API route
            const apiResponse = await axios.post(
                "/api/process",
                {
                    fileUrl: response.url, // Use response.url directly
                    name_to_search: name,
                },
                {
                    responseType: "blob",
                }
            );

            // Handle the ICS file download
            const url = window.URL.createObjectURL(
                new Blob([apiResponse.data])
            );
            const link = document.createElement("a");
            link.href = url;
            link.setAttribute("download", "shifts.ics");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            setUploadStatus("File processed and downloaded successfully!");
        } catch (error) {
            setUploadStatus(`Error: ${(error as Error).message}`);
        }
    };

    return (
        <div className="flex justify-center items-center h-screen bg-gray-200">
            <div className="bg-white p-8 rounded-lg shadow-md text-center max-w-sm w-full">
                <h1 className="text-2xl font-bold text-gray-800">
                    Shift Calendar
                </h1>
                <p className="text-gray-600 mt-2">
                    Upload an Excel file containing your work shifts and
                    generate an ICS calendar file.
                </p>
                <p className="mt-2">
                    <a
                        href="https://github.com/leele2/ts_xlxs_to_ics"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-500 hover:underline"
                    >
                        Learn More
                    </a>
                </p>
                <h2 className="text-xl font-semibold text-gray-800 mt-6">
                    Upload Your File
                </h2>
                <form id="uploadForm" className="mt-4" onSubmit={handleSubmit}>
                    <label
                        htmlFor="name_to_search"
                        className="block text-gray-700 text-left"
                    >
                        Name:
                    </label>
                    <input
                        type="text"
                        id="name_to_search"
                        name="name_to_search"
                        required
                        className="w-full p-2 mt-1 border border-gray-300 rounded-md"
                    />

                    <label
                        htmlFor="fileInput"
                        className="block text-gray-700 text-left mt-4"
                    >
                        Upload File:
                    </label>
                    <input
                        type="file"
                        id="fileInput"
                        name="excel_file"
                        accept=".xlsx"
                        required
                        className="w-full mt-1 border border-gray-300 rounded-md file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-white file:bg-gray-500 file:hover:bg-gray-600 file:cursor-pointer"
                    />

                    <button
                        type="submit"
                        className="w-full mt-4 bg-blue-500 text-white py-2 rounded-md text-lg transition duration-300 hover:bg-blue-700"
                    >
                        Upload
                    </button>
                </form>
                <p id="uploadStatus" className="text-gray-600 mt-4">
                    {uploadStatus}
                </p>
            </div>
        </div>
    );
}
