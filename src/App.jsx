import { useState } from 'react'
import './App.css'
import DomainAndResume from './assets/Components/DomainAndResume'
import ChatInterface from './assets/Components/Screen2/ChatInterface'
import SplitScreen from './assets/Components/SplitScreen'
import FeedbackScreen from './assets/Components/FeedbackScreen'

function App() {
  const [screen, setScreen] = useState('domainResume');
  const [domainData, setDomainData] = useState({
    domain: '',
    resumeText: ''
  });
  const [scores, setScores] = useState(null);

  const handleDomainResumeNext = (domain, resumeText) => {
    setDomainData({
      domain,
      resumeText
    });
    setScreen('interview');
  };

  const handleInterviewComplete = (interviewScores) => {
    // This function would be called when the interview is complete
    // You could generate real scores based on interview performance
    // For now, we'll use mock scores if none are provided
    setScores(interviewScores || {
      technicalSkills: Math.floor(Math.random() * 20) + 70, // Random score between 70-90
      softSkills: Math.floor(Math.random() * 30) + 65,      // Random score between 65-95
      problemSolving: Math.floor(Math.random() * 25) + 68,  // Random score between 68-93
    });
    setScreen('feedback');
  };

  const handleFinish = () => {
    // Reset everything and go back to first screen
    setDomainData({
      domain: '',
      resumeText: ''
    });
    setScores(null);
    setScreen('domainResume');
  };

  return (
    <>
      {screen === 'domainResume' && (
        <DomainAndResume onNext={handleDomainResumeNext} />
      )}
      {screen === 'interview' && (
        <SplitScreen 
          domain={domainData.domain} 
          resumetext={domainData.resumeText} 
          onComplete={handleInterviewComplete} 
        />
      )}
      {screen === 'feedback' && (
        <FeedbackScreen 
          scores={scores}
          domain={domainData.domain}
          onFinish={handleFinish}
        />
      )}
    </>
  )
}

export default App

// ---------------------------------------

