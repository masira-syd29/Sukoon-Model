"use client";

import { useState, useRef  } from "react";
import axios from "axios";

export default function Home() {
  const [text, setText] = useState("");
  const [response, setResponse] = useState("");
  const [emotions, setEmotions] = useState("");

  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const [transcribedAudio, setTranscribedAudio] = useState("");

  async function callGemini(emotion: string) {
    console.log("Calling Gemini with emotion:", emotion);

    const res = await fetch("http://localhost:8000/gemini", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        system_instruction: `You are a psychiatrist. The patient is experiencing this emotion: ${emotion}. Respond empathetically.`,
        contents: text,
        emotion, // no need to pass since alreday passed in system instruction
      }),
    });

    const data = await res.json();
    console.log("Gemini says:", data);
    setResponse(data.response);
  }

  async function detectEmotions() {
    const res = await fetch("http://localhost:8000/emotion_detection", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: text,
        system_instruction: "You are a psychiatrist. Your task is ONLY to identify the patient's primary emotion from their text. Do not write explanations or extra text.",
        emotion: "",
      }),
    });

    const data = await res.json();
    console.log("Emotions detected", data);

    // backend sends EmotionResponse { emotion, suggestions(well do later for now //) }
    setEmotions(data.emotion);
    callGemini(data.emotion); //pass directly to Gemini
  }

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorderRef.current = mediaRecorder;
    audioChunksRef.current = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
      }
    };

    mediaRecorder.start();
    setIsRecording(true);
    console.log("resording started")
  };

  const stopRecording = () => {
    console.log("resording stopped")
    return new Promise<void>((resolve) => {
      if (!mediaRecorderRef.current) return;

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        const file = new File([audioBlob], "recording.wav", { type: "audio/wav" });

        // send to backend
        const formData = new FormData();
        formData.append("audio", file);

        const res = await fetch("http://localhost:8000/stt", {
          method: "POST",
          body: formData,
        });

        const data = await res.json();
        console.log("Transcribed text:", data);
        setTranscribedAudio(data.text)
        resolve();
      };

      mediaRecorderRef.current.stop();
      setIsRecording(false);
    });
  };

  return (
    <main className="p-6">
      <h1 className="text-3xl font-bold">Sukoon - Mental Wellness</h1>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="How are you feeling?"
        className="border w-full p-2 mt-4"
      />
      <button
        onClick={detectEmotions}
        className="bg-blue-500 text-white px-4 py-2 mt-4"
      >
        Analyze
      </button>

      <div className="flex gap-4">
      {!isRecording ? (
        <button onClick={startRecording} className="p-2 bg-green-500 text-white rounded">
          🎤 Start Recording
        </button>
      ) : (
        <button onClick={stopRecording} className="p-2 bg-red-500 text-white rounded">
          ⏹ Stop Recording
        </button>
      )}
    </div>

      {response && (
        <div className="mt-6 p-4 bg-black rounded">
          <h2 className="font-semibold">Advice:</h2>
          <p>{response}</p>
        </div>
      )}
      {transcribedAudio && (
        <div className="mt-6 p-4 bg-black rounded">
          <h2 className="font-semibold">Advice:</h2>
          <p>{transcribedAudio}</p>
        </div>
      )}
    </main>
  );
}
