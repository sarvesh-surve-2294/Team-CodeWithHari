
// code for passing info to screen 2 
import { useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
// Use a CDN URL that matches your installed pdfjs-dist version (adjust as needed)
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://unpkg.com/pdfjs-dist@4.10.38/build/pdf.worker.mjs';

export default function DomainAndResume({ onNext }) {
  const [domain, setDomain] = useState('');
  const [resume, setResume] = useState(null);
  const [resumeText, setResumeText] = useState('');
  const [showExtracted, setShowExtracted] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState('');

  const domains = [
    'Artificial Intelligence',
    'Web Development',
    'Data Science',
    'Cybersecurity',
    'Cloud Computing'
  ];

  // Extract text from the uploaded PDF
  const extractTextFromPDF = async (file) => {
    setIsExtracting(true);
    setError('');
    
    const reader = new FileReader();
    reader.readAsArrayBuffer(file);
    
    reader.onload = async () => {
      try {
        const typedarray = new Uint8Array(reader.result);
        const pdf = await pdfjsLib.getDocument(typedarray).promise;
        let text = '';
        
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const content = await page.getTextContent();
          text += content.items.map(item => item.str).join(' ') + '\n';
        }
        
        setResumeText(text);
        setIsExtracting(false);
      } catch (err) {
        console.error('Error processing PDF:', err);
        setError('Failed to extract text from PDF. Please try another file.');
        setIsExtracting(false);
      }
    };
    
    reader.onerror = (error) => {
      console.error('Error reading file:', error);
      setError('Failed to read the file.');
      setIsExtracting(false);
    };
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        setError('Please upload a PDF file only.');
        return;
      }
      setResume(file);
      extractTextFromPDF(file);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!domain) {
      setError('Please select a domain.');
      return;
    }
    
    if (!resumeText) {
      setError('Please upload a resume with extractable text.');
      return;
    }
    
    // Pass the domain and resumeText to the parent component
    console.log(domain, resumeText); // For debugging
    if (onNext) {
      onNext(domain, resumeText);
    } else {
      // If onNext isn't provided, show extracted info
      setShowExtracted(true);
    }
  };

  // If the user has clicked Next and we have extracted text, show it
  if (showExtracted) {
    console.log(domain, resumeText);
    // This is just for debugging, as we'll use onNext prop
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-[#171717] text-white w-full h-screen">
      <div className="p-8 rounded-2xl shadow-lg w-full max-w-4xl">
        <h1 className="text-2xl font-bold mb-8 text-center">Select Domain & Upload Resume</h1>
        
        {error && (
          <div className="mb-4 p-3 bg-red-900/50 border border-red-500 rounded-xl text-red-200">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <label className="block mb-6">
            <span className="font-semibold">Select a Domain :</span>
            <div className="mt-2 relative">
              <input
                type="text"
                placeholder="Search or select a domain..."
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                list="domain-list"
                className="p-2 w-full border rounded-xl bg-black text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <datalist id="domain-list">
                {domains.map((d) => (
                  <option key={d} value={d} />
                ))}
              </datalist>
            </div>
          </label>

          <label className="block mb-6">
            <span className="font-semibold">Upload Resume (PDF only) :</span>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="mt-2 p-2 w-full border rounded-xl bg-black text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {isExtracting && (
              <p className="mt-2 text-blue-400">Extracting text from PDF...</p>
            )}
            {resumeText && !isExtracting && (
              <p className="mt-2 text-green-400">✓ Text extracted successfully</p>
            )}
          </label>

          <div className="flex justify-center mt-6">
            <button
              type="submit"
              disabled={isExtracting}
              className={`w-32 bg-blue-600 text-white p-3 rounded-2xl hover:bg-blue-700 transition duration-300 ${
                isExtracting ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {isExtracting ? 'Processing...' : 'Next ➜'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------
