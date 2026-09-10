import React, { useState, useEffect, useRef } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { getPdfChatStyles } from '../../styles/appStyles';
import apiClient from '../../api/apiClient';

const ChatAndAnalysisSection = ({
    loading, analysisResult, onInsightClick,
    translatedInsights, setTranslatedInsights, sessionId,
    selectionInsights, isSelectionLoading, activeTab, setActiveTab,
    userToken
}) => {
  const { currentTheme } = useTheme();
  const styles = getPdfChatStyles(currentTheme);
  const insightsPanelRef = useRef(null);

  const [isPodcastLoading, setIsPodcastLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [podcastLanguage, setPodcastLanguage] = useState('en');

  const [isTranslatingAll, setIsTranslatingAll] = useState(false);
  const [translationError, setTranslationError] = useState('');
  
  // 1. Track local translations and a manual override to force English
  const [localTranslated, setLocalTranslated] = useState(null);
  const [forceEnglish, setForceEnglish] = useState(false);

  useEffect(() => {
    if (insightsPanelRef.current) insightsPanelRef.current.scrollTop = 0;
  }, [analysisResult, translatedInsights, selectionInsights, activeTab, localTranslated]);

  const handleTranslateToHindi = async () => {
    if (!sessionId) return;
    setIsTranslatingAll(true);
    setTranslationError('');
    setForceEnglish(false); // Clear the English override
    
    try {
        const response = await apiClient.post('/translate-insights/', { sessionId });        
        let rawData = response.data.translated_analysis || response.data.translated_insights || response.data;        
        
        if (typeof rawData === 'string') {
            try { rawData = JSON.parse(rawData); } catch (e) {}
        }
        
        const extractedInsights = rawData.llm_insights || rawData;        
        
        const mergedInsights = {
            ...analysisResult?.llm_insights,
            ...extractedInsights
        };
        
        setLocalTranslated(mergedInsights);
        
        if (typeof setTranslatedInsights === 'function') {
            setTranslatedInsights(mergedInsights);
        }
        
    } catch (err) {
        setTranslationError('Failed to translate insights to Hindi.');
        console.error("Translation error:", err);
    } finally {
        setIsTranslatingAll(false);
    }
  };

  const handleShowOriginal = () => {
      setForceEnglish(true); // Force the UI back to English
      setLocalTranslated(null);
      if (typeof setTranslatedInsights === 'function') {
          setTranslatedInsights(null);
      }
  };

  const handleGeneratePodcast = async () => {
    if (!analysisResult) return;
    setIsPodcastLoading(true);
    setAudioUrl(null);
    try {
        const response = await apiClient.post('/generate-podcast/', {
            analysis_data: analysisResult,
            language: podcastLanguage
        }, { 
            responseType: 'blob',
        });

        const url = URL.createObjectURL(response.data);
        setAudioUrl(url);

    } catch (err) {
        console.error("Error generating podcast:", err);
    } finally {
        setIsPodcastLoading(false);
    }
  };

  // 2. Identify the active translation (Checking local state OR directly from the refreshed backend session!)
  const activeTranslationData = forceEnglish ? null : (localTranslated || translatedInsights || analysisResult?.translated_analysis);
  
  // 3. Extract BOTH the llm_insights and the top_sections so the entire page translates
  const displayInsights = activeTranslationData?.llm_insights || activeTranslationData || analysisResult?.llm_insights;
  const displayTopSections = activeTranslationData?.top_sections || analysisResult?.top_sections;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
        <div style={styles.tabsContainer}>
            <button
                style={{...styles.tabButton, ...(activeTab === 'analysis' && styles.activeTab)}}
                onClick={() => setActiveTab('analysis')}
            >
                Generated Insights
            </button>
            <button
                style={{...styles.tabButton, ...(activeTab === 'selection' && styles.activeTab)}}
                onClick={() => setActiveTab('selection')}
            >
                Selection Insights
            </button>
        </div>

        <div ref={insightsPanelRef} className="insights-panel" style={styles.insightsPanel}>
            {activeTab === 'analysis' && analysisResult && (
                <div style={styles.analysisResult}>
                    <h4 style={{marginBottom: "0rem", marginTop: "0.2rem"}}>Initial Insights:</h4>
                      {/* 4. Map over displayTopSections so they translate too! */}
                      {displayTopSections?.slice(0, 5).map((section, idx) => (
                          <div key={idx} style={styles.analysisSnippet} onClick={() => onInsightClick(section)}>
                              <p style={styles.analysisReason}><strong>From {section.document}:</strong> {section.reasoning}</p>
                              <p style={styles.sectionTitleText}>Section: "{section.section_title}"</p>
                              <p>{section.subsection_analysis}</p>
                              <div style={styles.snippetFooter}>
                                  <small>Page: {section.page_number > 0 ? section.page_number : 'N/A'}</small>
                              </div>
                          </div>
                      ))}

                    {displayInsights && (
                        <div style={styles.llmInsightsContainer}>
                            <div style={styles.insightsHeader}>
                                <h4 style={{ display: "flex", alignItems: "center", gap: "0.4rem", margin: "0rem", fontSize: "1.1rem", fontWeight: "600" }}>
                                Insights Bulb 💡
                                </h4>
                                <div style={styles.translateAllContainer}>
                                    {isTranslatingAll && <span style={{fontSize: '0.9rem', marginRight: '8px'}}>Translating...</span>}
                                    {/* 5. The button relies on activeTranslationData to flip correctly */}
                                    {activeTranslationData ? (
                                        <button onClick={handleShowOriginal} style={styles.showOriginalButton}>Show Original</button>
                                    ) : (
                                        <button onClick={handleTranslateToHindi} style={styles.button} disabled={isTranslatingAll || loading}>
                                            Translate to Hindi
                                        </button>
                                    )}
                                </div>
                            </div>
                            {translationError && <p style={{color: 'red'}}>{translationError}</p>}
                            {displayInsights && (
                                <>
                                    {displayInsights.key_insights?.length > 0 && (
                                        <div style={styles.insightCategory}>
                                            <h6 style={styles.insightCategoryTitle}>Key Insights</h6>
                                            <ul>{displayInsights.key_insights.map((item, i) => <li key={i}>{item}</li>)}</ul>
                                        </div>
                                    )}
                                    {displayInsights.did_you_know?.length > 0 && (
                                        <div style={styles.insightCategory}>
                                            <h6 style={styles.insightCategoryTitle}>Did You Know?</h6>
                                            <ul>{displayInsights.did_you_know.map((item, i) => <li key={i}>{item}</li>)}</ul>
                                        </div>
                                    )}
                                    {displayInsights.cross_document_connections?.length > 0 && (
                                        <div style={styles.insightCategory}>
                                            <h6 style={styles.insightCategoryTitle}>Connections Across Documents</h6>
                                            <ul>{displayInsights.cross_document_connections.map((item, i) => <li key={i}>{item}</li>)}</ul>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    )}
                    <div style={styles.podcastContainer}>
                        <div style={styles.podcastControls}>
                            <button onClick={handleGeneratePodcast} style={styles.button} disabled={isPodcastLoading || loading}>{isPodcastLoading ? 'Generating...' : '🎧 Generate Podcast'}</button>
                            <select value={podcastLanguage} onChange={e => setPodcastLanguage(e.target.value)} style={styles.languageSelector} disabled={isPodcastLoading || loading}>
                                <option value="en">English</option>
                                <option value="hi">Hindi</option>
                            </select>
                        </div>
                        {audioUrl && <audio controls src={audioUrl} style={styles.audioPlayer} />}
                    </div>
                </div>
            )}
            {activeTab === 'selection' && (
                <div style={styles.selectionInsightsContainer}>
                    {isSelectionLoading && <div style={styles.loadingIndicator}>Generating insights...</div>}
                    {selectionInsights && (
                        <div>
                            <div style={styles.insightCategory}>
                                <h6 style={styles.insightCategoryTitle}>Summary</h6>
                                <p>{selectionInsights.summary}</p>
                            </div>
                            <div style={styles.insightCategory}>
                                <h6 style={styles.insightCategoryTitle}>Key Takeaways</h6>
                                <ul>
                                    {selectionInsights.key_takeaways.map((item, i) => <li key={i}>{item}</li>)}
                                </ul>
                            </div>
                            <div style={styles.insightCategory}>
                                <h6 style={styles.insightCategoryTitle}>Potential Questions</h6>
                                <ul>
                                    {selectionInsights.potential_questions.map((item, i) => <li key={i}>{item}</li>)}
                                </ul>
                            </div>
                        </div>
                    )}
                    {!isSelectionLoading && !selectionInsights && (
                        <div style={styles.placeholderText}>
                            Select text in the PDF and click "Get Insights on Selection" to see details here.
                        </div>
                    )}
                </div>
            )}
        </div>
    </div>
  );
};

export default ChatAndAnalysisSection;