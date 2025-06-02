// frontend/app/components/ShiftCalendarUploader.tsx
"use client";

import { useState } from "react";
import axios from "axios";
import { upload } from "@vercel/blob/client";
import { Loader2, CloudUpload, CheckCircle, AlertTriangle } from "lucide-react";
import { GoogleLogin, googleLogout } from "@react-oauth/google";

export default function ShiftCalendarUploader() {
    const [uploadStatus, setUploadStatus] = useState<string>("");
    const [isLoading, setIsLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [step, setStep] = useState<number>(0);
    const [googleToken, setGoogleToken] = useState<string | undefined>(
        undefined
    );

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setIsLoading(true);
        setUploadStatus("Uploading file...");
        setStep(1);
        setError(null);
        setIsSuccess(false);

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

            setUploadStatus("File uploaded. Processing...");
            setStep(2);

            // Call the internal Next.js API route
            const apiResponse = await axios.post(
                "/api/process",
                {
                    fileUrl: response.url,
                    name_to_search: name,
                    google_token: googleToken,
                },
                {
                    responseType: "blob",
                }
            );

            const url = window.URL.createObjectURL(
                new Blob([apiResponse.data])
            );
            const link = document.createElement("a");
            link.href = url;
            link.setAttribute("download", "shifts.ics");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            setIsSuccess(true);
            setUploadStatus("File processed and downloaded successfully!");
            setStep(3);
        } catch (error) {
            const msg = (error as Error).message || "Something went wrong.";
            setError(msg);
            setUploadStatus(`Error: ${msg}`);
            setStep(0);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-800 to-slate-950 flex items-center justify-center p-6">
            <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl shadow-2xl p-10 w-full max-w-xl relative overflow-hidden">
                <div className="absolute -top-20 -right-20 w-64 h-64 bg-gradient-to-tr from-blue-500 to-purple-600 opacity-20 rounded-full blur-3xl animate-pulse"></div>
                <div className="text-center z-10 relative">
                    <h1 className="text-4xl font-extrabold text-white drop-shadow-xl mb-2 animate-fade-in">
                        🚀 Shift Calendar Uploader
                    </h1>
                    <p className="text-gray-300 mb-4">
                        Upload an Excel file and get your ICS calendar file in
                        seconds.
                    </p>
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label
                                htmlFor="name_to_search"
                                className="text-left block text-gray-300 text-sm font-semibold mb-1"
                            >
                                Your Name
                            </label>
                            <input
                                type="text"
                                id="name_to_search"
                                name="name_to_search"
                                required
                                className="w-full px-4 py-2 bg-white/10 border border-gray-500 rounded-lg text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400"
                                placeholder="e.g. John Doe"
                            />
                        </div>
                        <div>
                            <label
                                htmlFor="fileInput"
                                className="text-left block text-gray-300 text-sm font-semibold mb-1"
                            >
                                Upload Excel File
                            </label>
                            <input
                                type="file"
                                id="fileInput"
                                name="excel_file"
                                accept=".xlsx"
                                required
                                className="w-full file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-white file:bg-gradient-to-r file:from-blue-500 file:to-purple-600 file:hover:opacity-90 file:transition-all file:duration-300 file:cursor-pointer text-white"
                            />
                        </div>
                        <GoogleLogin
                            onSuccess={(credentialResponse) => {
                                const token = credentialResponse.credential;
                                // store token in state or pass during API request
                                setGoogleToken(token);
                            }}
                            onError={() => {
                                console.log("Login Failed");
                            }}
                        />
                        <button
                            type="submit"
                            className={`flex items-center justify-center w-full px-4 py-3 rounded-xl font-bold transition-all duration-300 text-white ${
                                isLoading
                                    ? "bg-gradient-to-r from-yellow-500 to-yellow-700 animate-pulse"
                                    : isSuccess
                                    ? "bg-gradient-to-r from-green-500 to-emerald-600"
                                    : "bg-gradient-to-r from-blue-600 to-purple-700 hover:scale-105"
                            }`}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />{" "}
                                    {uploadStatus}
                                </>
                            ) : isSuccess ? (
                                <>
                                    <CheckCircle className="mr-2 h-5 w-5" />{" "}
                                    Success!
                                </>
                            ) : error ? (
                                <>
                                    <AlertTriangle className="mr-2 h-5 w-5" />{" "}
                                    Retry
                                </>
                            ) : (
                                <>
                                    <CloudUpload className="mr-2 h-5 w-5" />{" "}
                                    Upload File
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-6 text-sm text-gray-400 text-left">
                        {step > 0 && (
                            <div className="flex items-center gap-3">
                                <div className="flex-1 bg-gray-700 rounded-full h-2 overflow-hidden">
                                    <div
                                        className={`h-full rounded-full ${
                                            step === 1
                                                ? "bg-yellow-400 w-1/3 animate-pulse"
                                                : step === 2
                                                ? "bg-blue-500 w-2/3 animate-pulse"
                                                : "bg-green-500 w-full"
                                        }`}
                                    ></div>
                                </div>
                                <span className="text-xs">
                                    Step {step} of 3
                                </span>
                            </div>
                        )}
                    </div>

                    <div className="mt-6 text-gray-400 text-xs">
                        Curious how it works?{" "}
                        <a
                            href="https://github.com/leele2/ts_xlxs_to_ics"
                            className="underline hover:text-blue-400"
                        >
                            View on GitHub
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
}
