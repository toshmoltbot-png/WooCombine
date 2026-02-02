/**
 * DraftBoard - Big screen display for in-person drafts
 * Optimized for TV/projector display
 */

import React, { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useDraft, useDraftPicks, useDraftTeams } from '../../hooks/useDraft';
import LoadingScreen from '../../components/LoadingScreen';

const DraftBoard = () => {
  const { draftId } = useParams();
  
  const { draft, loading: draftLoading } = useDraft(draftId);
  const { picks } = useDraftPicks(draftId);
  const { teams } = useDraftTeams(draftId);

  // Group picks by team for board display
  const picksByTeam = useMemo(() => {
    const grouped = {};
    teams.forEach(team => {
      grouped[team.id] = [];
    });
    picks.forEach(pick => {
      if (grouped[pick.team_id]) {
        grouped[pick.team_id].push(pick);
      }
    });
    return grouped;
  }, [picks, teams]);

  // Get current team
  const currentTeam = useMemo(() => {
    if (!draft?.current_team_id) return null;
    return teams.find(t => t.id === draft.current_team_id);
  }, [draft?.current_team_id, teams]);

  // Last pick info
  const lastPick = picks[picks.length - 1];
  const lastPickTeam = lastPick ? teams.find(t => t.id === lastPick.team_id) : null;

  if (draftLoading) return <LoadingScreen />;
  if (!draft) return <div className="p-8 text-center text-white bg-gray-900 min-h-screen">Draft not found</div>;

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Header */}
      <header className="text-center mb-8">
        <h1 className="text-4xl font-bold mb-2">{draft.name}</h1>
        <p className="text-xl text-gray-400">
          Round {draft.current_round} of {draft.num_rounds} • Pick #{draft.current_pick}
        </p>
      </header>

      {/* On The Clock */}
      {draft.status === 'active' && currentTeam && (
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl p-8 mb-8 text-center">
          <p className="text-blue-200 uppercase tracking-wider text-sm mb-2">On The Clock</p>
          <h2 className="text-5xl font-bold">{currentTeam.team_name}</h2>
          {currentTeam.coach_name && (
            <p className="text-blue-200 mt-2 text-xl">{currentTeam.coach_name}</p>
          )}
        </div>
      )}

      {/* Paused */}
      {draft.status === 'paused' && (
        <div className="bg-yellow-600 rounded-2xl p-8 mb-8 text-center">
          <h2 className="text-4xl font-bold">⏸️ DRAFT PAUSED</h2>
        </div>
      )}

      {/* Completed */}
      {draft.status === 'completed' && (
        <div className="bg-green-600 rounded-2xl p-8 mb-8 text-center">
          <h2 className="text-4xl font-bold">🏆 DRAFT COMPLETE</h2>
        </div>
      )}

      {/* Draft Board Grid */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              {teams.map(team => {
                const isOnClock = team.id === draft.current_team_id;
                return (
                  <th 
                    key={team.id}
                    className={`p-4 text-left border-b-2 ${
                      isOnClock 
                        ? 'bg-blue-600 border-blue-400' 
                        : 'bg-gray-800 border-gray-700'
                    }`}
                  >
                    <div className="font-bold text-lg">{team.team_name}</div>
                    {team.coach_name && (
                      <div className="text-sm opacity-70">{team.coach_name}</div>
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {/* Render rows for each round */}
            {Array.from({ length: draft.num_rounds || 10 }, (_, roundIdx) => {
              const round = roundIdx + 1;
              return (
                <tr key={round} className="border-b border-gray-800">
                  {teams.map(team => {
                    const teamPicks = picksByTeam[team.id] || [];
                    const pickForRound = teamPicks.find(p => p.round === round);
                    const isCurrentPick = draft.current_round === round && team.id === draft.current_team_id;
                    
                    return (
                      <td 
                        key={team.id}
                        className={`p-3 ${
                          isCurrentPick 
                            ? 'bg-blue-900 animate-pulse' 
                            : pickForRound 
                              ? 'bg-gray-800' 
                              : 'bg-gray-900'
                        }`}
                      >
                        {pickForRound ? (
                          <div className="font-medium">
                            {pickForRound.player?.name || `Player ${pickForRound.player_id?.slice(0, 8)}`}
                          </div>
                        ) : isCurrentPick ? (
                          <div className="text-blue-400 italic">Picking...</div>
                        ) : (
                          <div className="text-gray-600">—</div>
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Last Pick Banner */}
      {lastPick && lastPickTeam && (
        <div className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 p-4">
          <div className="max-w-4xl mx-auto text-center">
            <span className="text-gray-400">Last Pick: </span>
            <span className="font-bold text-lg">
              #{lastPick.pick_number} {lastPickTeam.team_name}
            </span>
            <span className="text-gray-400"> selected </span>
            <span className="font-bold text-green-400">
              {lastPick.player?.name || 'Player'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default DraftBoard;
