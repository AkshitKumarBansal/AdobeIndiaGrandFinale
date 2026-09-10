// import React, { useState, useEffect } from "react";
// import { useTheme } from "../../contexts/ThemeContext";
// import { getPdfChatStyles } from "../../styles/appStyles";
// import { MenuIcon } from "../common/Icons";
// import apiClient from "../../api/apiClient";

// const SessionHistorySidebar = ({
//   onSelectSession,
//   onNewChat,
//   activeSessionId,
//   userToken,
// }) => {
//   const [sessions, setSessions] = useState([]);
//   const [isLoading, setIsLoading] = useState(true);
//   const { currentTheme } = useTheme();
//   const styles = getPdfChatStyles(currentTheme);
//   const [isOpen, setIsOpen] = useState(false);

//   useEffect(() => {
//     if (!userToken) return;
//     const fetchSessions = async () => {
//       setIsLoading(true);
//       try {
//         const response = await apiClient.get("/sessions/");
//         const sortedSessions = response.data.sort(
//           (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
//         );
//         setSessions(sortedSessions);
//       } catch (error) {
//         console.error("Failed to fetch sessions:", error);
//       } finally {
//         setIsLoading(false);
//       }
//     };
//     fetchSessions();
//   }, [activeSessionId, userToken]);

//   return (
//     <div className={`history-sidebar ${isOpen ? 'open' : 'collapsed'}`}>
//       <div style={{ ...styles.historyHeader, paddingBottom: "0.5rem" }}>
//         <span
//           style={{ cursor: "pointer", paddingTop: "0.5rem" }}
//           onClick={() => setIsOpen((prev) => !prev)}
//         >
//           <MenuIcon />
//         </span>
//         {isOpen && <h3 style={styles.historyTitle}>Chat History</h3>}
//       </div>

//       {isOpen && (
//         <div
//           className="session-list"
//           style={{
//             ...styles.sessionList,
//           }}
//         >
//           <button onClick={onNewChat} className="new-chat-inline">
//             + New Chat
//           </button>
//           {isLoading ? (
//             <p>Loading history...</p>
//           ) : (
//             sessions.map((session) => (
//               <div
//                 key={session.id}
//                 onClick={() => onSelectSession(session.id)}
//                 style={{
//                   ...styles.sessionItem,
//                   ...(session.id === activeSessionId &&
//                     styles.activeSessionItem),
//                 }}
//               >
//                 <p style={styles.sessionPersona}>
//                   {session.persona || "Untitled Chat"}
//                 </p>
//                 <p style={styles.sessionJob}>{session.job}</p>
//                 <p style={styles.sessionTimestamp}>
//                   {new Date(session.timestamp).toLocaleString()}
//                 </p>
//               </div>
//             ))
//           )}
//         </div>
//       )}
//     </div>
//   );
// };

// export default SessionHistorySidebar;


import React, { useState, useEffect } from "react";
import { useTheme } from "../../contexts/ThemeContext";
import { getPdfChatStyles } from "../../styles/appStyles";
import { MenuIcon } from "../common/Icons";
import apiClient from "../../api/apiClient";

const SessionHistorySidebar = ({
  onSelectSession,
  onNewChat,
  activeSessionId,
  userToken,

  sessionUpdateKey, // FIX: Accept the new prop

}) => {
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const { currentTheme } = useTheme();
  const styles = getPdfChatStyles(currentTheme);
  const [isOpen, setIsOpen] = useState(false); // FIX: Added state declaration


  useEffect(() => {
    if (!userToken) return;
    const fetchSessions = async () => {
      setIsLoading(true);
      try {
        const response = await apiClient.get("/sessions/");
        // FIX: Ensure data is an array before sorting to prevent crashes
        const sortedSessions = Array.isArray(response.data) 
          ? response.data.sort(
              (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
            )
          : [];
        setSessions(sortedSessions);
      } catch (error)
      {
        console.error("Failed to fetch sessions:", error);
        setSessions([]); // Set to empty array on error to prevent crashes
      } finally {
        setIsLoading(false);
      }
    };
    fetchSessions();
    // FIX: Add sessionUpdateKey to the dependency array to trigger refetch
  }, [activeSessionId, userToken, sessionUpdateKey]); 

  return (
    <div className={`history-sidebar ${isOpen ? 'open' : 'collapsed'}`}>
      <div style={{ ...styles.historyHeader, paddingBottom: "0.5rem" }}>
        <span
          style={{ cursor: "pointer", paddingTop: "0.5rem" }}
          onClick={() => setIsOpen((prev) => !prev)}
        >
          <MenuIcon />
        </span>
        {isOpen && <h3 style={styles.historyTitle}>Chat History</h3>}
      </div>

      {isOpen && (
        <div
          className="session-list"
          style={{
            ...styles.sessionList,
          }}
        >
          <button onClick={onNewChat} className="new-chat-inline">
            + New Chat
          </button>
          {isLoading ? (
            <p>Loading history...</p>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                style={{
                  ...styles.sessionItem,
                  ...(session.id === activeSessionId &&
                    styles.activeSessionItem),
                }}
              >
                <p style={styles.sessionPersona}>
                  {session.persona || "Untitled Chat"}
                </p>
                <p style={styles.sessionJob}>{session.job}</p>
                <p style={styles.sessionTimestamp}>
                  {new Date(session.timestamp).toLocaleString()}
                </p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default SessionHistorySidebar;