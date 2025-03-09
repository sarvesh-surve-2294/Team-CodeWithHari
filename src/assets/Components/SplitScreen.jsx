import { useEffect, useRef, useState } from "react";
import ChatInterface from "./Screen2/ChatInterface";

export default function SplitScreen({domain, resumetext, onComplete}) {
  const videoRef = useRef(null);
  const [cameraError, setCameraError] = useState(false);
  const [messageCount, setMessageCount] = useState(0);
  const [interviewComplete, setInterviewComplete] = useState(false);

  useEffect(() => {
    const startWebcam = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
        });
        // Check if the stream is active and has video tracks
        if (!stream || !stream.active || !stream.getVideoTracks().length) {
          throw new Error("Webcam not available");
        }
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (error) {
        console.error("Error accessing webcam:", error);
        setCameraError(true);
      }
    };
    startWebcam();
  }, []);

  const handleMessageCountUpdate = (count) => {
    setMessageCount(count);
    // Enable complete button after a sufficient number of exchanges (for example, 6 messages)
    if (count >= 3 && !interviewComplete) {
      setInterviewComplete(true);
    }
  };

  const handleCompleteInterview = () => {
    // Stop the webcam
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
    }
    // Call the onComplete callback to move to the feedback screen
    if (onComplete) {
      onComplete();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#171717] overflow-hidden">
      <div className="flex flex-grow overflow-hidden">
        {/* Left Section - Webcam */}
        <div className="w-1/2 bg-black flex items-center justify-center relative">
          {cameraError ? (
            <p className="text-white text-xl">
              Error accessing camera. Please check your webcam settings.
            </p>
          ) : (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="w-full h-full object-cover transform scale-x-[-1]"
            />
          )}
          {/* Interview status indicator */}
          <div className="absolute top-4 left-4 bg-[#1e1e1e] px-3 py-1 rounded-md border border-gray-700">
            <p className="text-white flex items-center">
              <span className={`inline-block w-3 h-3 rounded-full mr-2 ${messageCount > 0 ? "bg-green-500" : "bg-gray-500"}`}></span>
              Interview {messageCount > 0 ? "Active" : "Ready"}
            </p>
          </div>
        </div>

        {/* Right Section - Chat Interface - This should have its own scroll */}
        <div className="w-1/2 overflow-hidden">
          <ChatInterface
            domain={domain}
            resumeText={resumetext}
            onMessageCountUpdate={handleMessageCountUpdate}
          />
        </div>
      </div>

      {/* Complete Interview Button */}
      <div className="p-4 bg-[#1e1e1e] border-t border-gray-700 flex justify-center">
        <button
          onClick={handleCompleteInterview}
          disabled={!interviewComplete}
          className={`px-6 py-3 rounded-lg font-bold text-white ${
            interviewComplete
              ? "bg-green-600 hover:bg-green-700"
              : "bg-gray-600 cursor-not-allowed opacity-50"
          } transition duration-300`}
        >
          {interviewComplete ? "Complete Interview" : "Answer More Questions to Complete"}
        </button>
      </div>
    </div>
  );
}

// -------------------------------------------------
