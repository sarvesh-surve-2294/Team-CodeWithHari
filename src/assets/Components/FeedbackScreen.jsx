import React from 'react';

function FeedbackScreen({ scores, domain, onFinish }) {
  // Default scores if not provided
  const defaultScores = {
    technicalSkills: 50,
    softSkills: 50,
    problemSolving: 50,
  };

  // Use provided scores or defaults
  const finalScores = scores || defaultScores;

  // Calculate total score (average of all three)
  const totalScore = Math.round(
    (finalScores.technicalSkills + finalScores.softSkills + finalScores.problemSolving) / 3
  );

  // Function to determine color based on score
  const getScoreColor = (score) => {
    if (score >= 80) return "text-green-500";
    if (score >= 60) return "text-yellow-500";
    return "text-red-500";
  };

  // Function to get feedback based on score range - no longer hardcoded strings
  const getFeedback = (score) => {
    const feedbackRanges = [
      { min: 80, label: "Excellent" },
      { min: 70, label: "Good" },
      { min: 60, label: "Satisfactory" },
      { min: 50, label: "Needs Improvement" },
      { min: 0, label: "Insufficient" }
    ];
    
    return feedbackRanges.find(range => score >= range.min).label;
  };

  // Function to generate detailed feedback for each skill area
  const getDetailedFeedback = (skillType, score) => {
    const feedbackMap = {
      technicalSkills: {
        excellent: `Your technical skills in ${domain} are excellent. You've demonstrated comprehensive understanding and advanced proficiency in key concepts.`,
        good: `Your technical skills in ${domain} demonstrate good proficiency. You've shown strong understanding of key concepts.`,
        satisfactory: `Your technical skills in ${domain} meet the basic requirements. Some areas could benefit from deeper understanding.`,
        needsImprovement: `There are several areas in ${domain} technical knowledge that need improvement. Consider focusing on core concepts.`,
        insufficient: `Your technical knowledge in ${domain} doesn't meet the minimum requirements. We recommend studying the fundamentals.`
      },
      softSkills: {
        excellent: "Your communication was exceptional, showing clear articulation and professional demeanor throughout the interview.",
        good: "Your communication was clear and professional. You articulated your thoughts well during the interview.",
        satisfactory: "Your communication skills are adequate for the role, though more clarity would be beneficial in some areas.",
        needsImprovement: "Your communication could be more effective. Work on clarity and professional articulation of your ideas.",
        insufficient: "Your communication skills need significant improvement to meet professional standards."
      },
      problemSolving: {
        excellent: "You demonstrated excellent problem-solving abilities with innovative approaches and efficient solutions.",
        good: "You demonstrated good problem-solving abilities, approaching challenges methodically.",
        satisfactory: "Your problem-solving approach is functional, though could benefit from more structured methodology.",
        needsImprovement: "Work on improving your problem-solving approach. Try to be more analytical when facing technical challenges.",
        insufficient: "Your problem-solving skills need significant development to meet the requirements of this position."
      }
    };
    
    let feedbackLevel;
    if (score >= 80) feedbackLevel = "excellent";
    else if (score >= 70) feedbackLevel = "good";
    else if (score >= 60) feedbackLevel = "satisfactory";
    else if (score >= 50) feedbackLevel = "needsImprovement";
    else feedbackLevel = "insufficient";
    
    return feedbackMap[skillType][feedbackLevel];
  };

  // Create custom progress bar component
  const ProgressBar = ({ percentage, label, color }) => (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-2">
        <span className="text-lg font-semibold text-gray-200">{label}</span>
        <span className={`text-xl font-bold ${getScoreColor(percentage)}`}>
          {percentage}%
        </span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-4">
        <div
          className={`h-4 rounded-full ${color}`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
      <div className="mt-1 text-right text-gray-400">
        {getFeedback(percentage)}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#171717] text-white flex flex-col">
      {/* Header */}
      <header className="bg-[#1e1e1e] p-6 border-b border-gray-700">
        <h1 className="text-3xl font-bold text-center">Interview Feedback</h1>
        <p className="text-gray-400 text-center mt-2">
          {domain} Position Assessment
        </p>
      </header>

      {/* Main content */}
      <div className="flex-grow p-8 max-w-4xl mx-auto w-full">
        {/* Overall score card */}
        <div className="bg-[#1e1e1e] rounded-lg p-6 mb-8 text-center border border-gray-700">
          <h2 className="text-2xl font-semibold mb-2">Overall Performance</h2>
          <div className={`text-6xl font-bold mb-3 ${getScoreColor(totalScore)}`}>
            {totalScore}%
          </div>
          <p className="text-xl text-gray-300">
            {getFeedback(totalScore)}
          </p>
        </div>

        {/* Individual scores */}
        <div className="bg-[#1e1e1e] rounded-lg p-6 border border-gray-700">
          <h2 className="text-2xl font-semibold mb-6">Detailed Assessment</h2>

          <ProgressBar
            percentage={finalScores.technicalSkills}
            label="Technical Skills"
            color="bg-blue-600"
          />

          <ProgressBar
            percentage={finalScores.softSkills}
            label="Communication Skills"
            color="bg-purple-600"
          />

          <ProgressBar
            percentage={finalScores.problemSolving}
            label="Problem Solving"
            color="bg-green-600"
          />

          {/* Feedback section - now using dynamic feedback generation */}
          <div className="mt-8 p-4 bg-[#252525] rounded border border-gray-700">
            <h3 className="text-xl font-semibold mb-3">Feedback Summary</h3>
            <p className="text-gray-300 mb-3">
              {getDetailedFeedback('technicalSkills', finalScores.technicalSkills)}
            </p>
            <p className="text-gray-300 mb-3">
              {getDetailedFeedback('softSkills', finalScores.softSkills)}
            </p>
            <p className="text-gray-300">
              {getDetailedFeedback('problemSolving', finalScores.problemSolving)}
            </p>
          </div>
        </div>

        {/* Action buttons */}
        <div className="mt-8 flex justify-center">
          <button
            onClick={onFinish}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300"
          >
            Finish & Return to Home
          </button>
        </div>
      </div>
    </div>
  );
}

export default FeedbackScreen;

// ---------------------------------------

