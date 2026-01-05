import { useState } from "react";
import "./styles.css";
import Header from "./components/Header";
import OverviewView from "./components/OverviewView";
import PlayersView from "./components/PlayersView";
import PlayerComparisonView from "./components/PlayerComparisonView";
import TeamComparisonView from "./components/TeamComparisonView";
import TeamsView from "./components/TeamsView";
import GamesView from "./components/GamesView";

export default function App() {
  const [activeView, setActiveView] = useState("overview");

  return (
    <div className="app-root">
      <Header activeView={activeView} onChangeView={setActiveView} />
      <main className="app-main">
        {activeView === "overview" && <OverviewView />}
        {activeView === "players" && <PlayersView />}
        {activeView === "compare" && <PlayerComparisonView />}
        {activeView === "compare-teams" && <TeamComparisonView />}
        {activeView === "teams" && <TeamsView />}
        {activeView === "games" && <GamesView />}
      </main>
      <footer className="app-footer">
        <span>NBA Analytics API</span>
        <span className="divider">•</span>
        <span>Backend v0.1.0</span>
      </footer>
    </div>
  );
}
