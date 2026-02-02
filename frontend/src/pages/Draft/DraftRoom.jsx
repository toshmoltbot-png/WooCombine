/**
 * DraftRoom - Live draft interface
 * Real-time draft picking with player pool, draft board, and team view
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { 
  useDraft, 
  useDraftPicks, 
  useDraftTeams, 
  useAvailablePlayers,
  useDraftActions,
  useCoachRankings
} from '../../hooks/useDraft';
import LoadingScreen from '../../components/LoadingScreen';
import { 
  Clock, 
  Users, 
  Trophy,
  Search,
  ChevronDown,
  Pause,
  Play,
  RotateCcw,
  Monitor,
  ArrowLeft
} from 'lucide-react';

const DraftRoom = () => {
  const { draftId } = useParams();
  const { user } = useAuth();
  const { showSuccess, showError } = useToast();
  
  const { draft, loading: draftLoading } = useDraft(draftId);
  const { picks } = useDraftPicks(draftId);
  const { teams } = useDraftTeams(draftId);
  const { players, refetch: refetchPlayers } = useAvailablePlayers(draftId);
  const { rankings } = useCoachRankings(draftId);
  const { makePick, pauseDraft, resumeDraft, undoPick, loading: actionLoading, error: actionError } = useDraftActions(draftId);

  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('composite');
  const [timeRemaining, setTimeRemaining] = useState(null);

  // Timer countdown
  useEffect(() => {
    if (!draft?.pick_deadline) {
      setTimeRemaining(null);
      return;
    }

    const deadline = new Date(draft.pick_deadline).getTime();
    
    const interval = setInterval(() => {
      const now = Date.now();
      const remaining = Math.max(0, Math.floor((deadline - now) / 1000));
      setTimeRemaining(remaining);
      
      if (remaining <= 0) {
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [draft?.pick_deadline]);

  // Refetch players when picks change
  useEffect(() => {
    refetchPlayers();
  }, [picks.length, refetchPlayers]);

  // Current team on the clock
  const currentTeam = useMemo(() => {
    if (!draft?.current_team_id || !teams.length) return null;
    return teams.find(t => t.id === draft.current_team_id);
  }, [draft?.current_team_id, teams]);

  // Is it my turn?
  const isMyTurn = useMemo(() => {
    if (!currentTeam || !user) return false;
    return currentTeam.coach_user_id === user.uid || draft?.created_by === user.uid;
  }, [currentTeam, user, draft?.created_by]);

  // Am I the admin?
  const isAdmin = draft?.created_by === user?.uid;

  // Filter and sort players
  const filteredPlayers = useMemo(() => {
    let result = [...players];

    // Search filter
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(p => 
        p.name?.toLowerCase().includes(q) ||
        p.number?.toString().includes(q)
      );
    }

    // Sort
    result.sort((a, b) => {
      // Prioritize ranked players if sorting by ranking
      if (sortBy === 'ranking') {
        const aRank = rankings.indexOf(a.id);
        const bRank = rankings.indexOf(b.id);
        if (aRank !== -1 && bRank !== -1) return aRank - bRank;
        if (aRank !== -1) return -1;
        if (bRank !== -1) return 1;
      }

      // Default composite score sort
      const aScore = a.composite_score ?? a.scores?.composite ?? 0;
      const bScore = b.composite_score ?? b.scores?.composite ?? 0;
      return bScore - aScore;
    });

    return result;
  }, [players, searchQuery, sortBy, rankings]);

  // Group picks by team
  const picksByTeam = useMemo(() => {
    const grouped = {};
    teams.forEach(team => {
      grouped[team.id] = picks.filter(p => p.team_id === team.id);
    });
    return grouped;
  }, [picks, teams]);

  // Handle pick
  const handlePick = async (playerId) => {
    if (!isMyTurn && !isAdmin) {
      showError("It's not your turn");
      return;
    }

    try {
      await makePick(playerId);
      showSuccess('Pick made!');
    } catch (err) {
      showError(err.message || 'Failed to make pick');
    }
  };

  // Handle pause/resume
  const handlePauseResume = async () => {
    try {
      if (draft.status === 'active') {
        await pauseDraft();
        showSuccess('Draft paused');
      } else {
        await resumeDraft();
        showSuccess('Draft resumed');
      }
    } catch (err) {
      showError(err.message);
    }
  };

  // Handle undo
  const handleUndo = async () => {
    if (!confirm('Undo the last pick?')) return;
    try {
      await undoPick();
      showSuccess('Pick undone');
    } catch (err) {
      showError(err.message);
    }
  };

  if (draftLoading) return <LoadingScreen />;
  if (!draft) return <div className="p-8 text-center">Draft not found</div>;

  const formatTime = (seconds) => {
    if (seconds === null) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to={`/events`} className="text-gray-500 hover:text-gray-700">
                <ArrowLeft size={20} />
              </Link>
              <div>
                <h1 className="text-xl font-bold">{draft.name}</h1>
                <p className="text-sm text-gray-500">
                  Round {draft.current_round} of {draft.num_rounds} • Pick #{draft.current_pick}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              {/* Draft Board Link */}
              <Link 
                to={`/draft/${draftId}/board`}
                className="flex items-center gap-2 px-3 py-2 text-sm bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                <Monitor size={16} />
                Draft Board
              </Link>

              {/* Admin Controls */}
              {isAdmin && (
                <>
                  <button
                    onClick={handlePauseResume}
                    className="flex items-center gap-2 px-3 py-2 text-sm bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200"
                    disabled={actionLoading}
                  >
                    {draft.status === 'active' ? <Pause size={16} /> : <Play size={16} />}
                    {draft.status === 'active' ? 'Pause' : 'Resume'}
                  </button>
                  <button
                    onClick={handleUndo}
                    className="flex items-center gap-2 px-3 py-2 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
                    disabled={actionLoading || picks.length === 0}
                  >
                    <RotateCcw size={16} />
                    Undo
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* On The Clock Banner */}
      {draft.status === 'active' && currentTeam && (
        <div className={`py-6 text-center ${isMyTurn ? 'bg-green-600' : 'bg-blue-600'} text-white`}>
          <p className="text-sm uppercase tracking-wide opacity-80">On The Clock</p>
          <h2 className="text-3xl font-bold mt-1">{currentTeam.team_name}</h2>
          {currentTeam.coach_name && (
            <p className="text-sm mt-1 opacity-80">{currentTeam.coach_name}</p>
          )}
          {timeRemaining !== null && (
            <div className="mt-3 flex items-center justify-center gap-2">
              <Clock size={20} />
              <span className={`text-2xl font-mono ${timeRemaining <= 10 ? 'text-red-300 animate-pulse' : ''}`}>
                {formatTime(timeRemaining)}
              </span>
            </div>
          )}
          {isMyTurn && (
            <p className="mt-2 text-green-200 font-semibold">Your pick!</p>
          )}
        </div>
      )}

      {/* Paused Banner */}
      {draft.status === 'paused' && (
        <div className="py-4 text-center bg-yellow-500 text-white">
          <p className="font-semibold">⏸️ Draft Paused</p>
        </div>
      )}

      {/* Completed Banner */}
      {draft.status === 'completed' && (
        <div className="py-4 text-center bg-green-600 text-white">
          <p className="font-semibold">🏆 Draft Complete!</p>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Available Players */}
          <div className="lg:col-span-2 bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="p-4 border-b">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold flex items-center gap-2">
                  <Users size={18} />
                  Available Players ({filteredPlayers.length})
                </h3>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="text-sm border rounded-lg px-2 py-1"
                >
                  <option value="composite">Sort: Composite</option>
                  <option value="ranking">Sort: My Ranking</option>
                  <option value="name">Sort: Name</option>
                </select>
              </div>
              <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search players..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm"
                />
              </div>
            </div>

            <div className="overflow-y-auto max-h-[500px]">
              <table className="w-full">
                <thead className="bg-gray-50 sticky top-0">
                  <tr className="text-left text-xs text-gray-500 uppercase">
                    <th className="px-4 py-2">Player</th>
                    <th className="px-4 py-2 text-center">Composite</th>
                    <th className="px-4 py-2 text-center">40m</th>
                    <th className="px-4 py-2 text-center">Vert</th>
                    <th className="px-4 py-2"></th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredPlayers.map((player, idx) => {
                    const rankIndex = rankings.indexOf(player.id);
                    const isRanked = rankIndex !== -1;
                    
                    return (
                      <tr 
                        key={player.id} 
                        className={`hover:bg-gray-50 ${isRanked ? 'bg-yellow-50' : ''}`}
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            {isRanked && (
                              <span className="text-xs bg-yellow-200 text-yellow-800 px-1.5 py-0.5 rounded">
                                #{rankIndex + 1}
                              </span>
                            )}
                            <div>
                              <p className="font-medium">{player.name}</p>
                              {player.number && (
                                <p className="text-xs text-gray-500">#{player.number}</p>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center font-semibold">
                          {(player.composite_score ?? player.scores?.composite)?.toFixed(1) ?? '-'}
                        </td>
                        <td className="px-4 py-3 text-center text-sm">
                          {(player.scores?.['40m_dash'] ?? player.drill_40m_dash)?.toFixed(2) ?? '-'}
                        </td>
                        <td className="px-4 py-3 text-center text-sm">
                          {(player.scores?.vertical_jump ?? player.vertical_jump)?.toFixed(1) ?? '-'}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => handlePick(player.id)}
                            disabled={!isMyTurn && !isAdmin || actionLoading || draft.status !== 'active'}
                            className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                              isMyTurn || isAdmin
                                ? 'bg-blue-600 text-white hover:bg-blue-700'
                                : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                            }`}
                          >
                            Draft
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              
              {filteredPlayers.length === 0 && (
                <div className="p-8 text-center text-gray-500">
                  No players available
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* My Team */}
            {teams.filter(t => t.coach_user_id === user?.uid).map(team => (
              <div key={team.id} className="bg-white rounded-xl shadow-sm overflow-hidden">
                <div className="p-4 border-b bg-blue-50">
                  <h3 className="font-semibold flex items-center gap-2">
                    <Trophy size={18} className="text-blue-600" />
                    My Team: {team.team_name}
                  </h3>
                </div>
                <div className="p-4">
                  {(picksByTeam[team.id] || []).length === 0 ? (
                    <p className="text-gray-500 text-sm">No picks yet</p>
                  ) : (
                    <ul className="space-y-2">
                      {(picksByTeam[team.id] || []).map((pick, idx) => (
                        <li key={pick.id} className="flex items-center justify-between text-sm">
                          <span className="text-gray-500">Rd {pick.round}</span>
                          <span className="font-medium">{pick.player?.name || pick.player_id}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            ))}

            {/* Recent Picks */}
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <div className="p-4 border-b">
                <h3 className="font-semibold">Recent Picks</h3>
              </div>
              <div className="p-4">
                {picks.length === 0 ? (
                  <p className="text-gray-500 text-sm">No picks yet</p>
                ) : (
                  <ul className="space-y-2">
                    {picks.slice(-8).reverse().map((pick) => {
                      const team = teams.find(t => t.id === pick.team_id);
                      return (
                        <li key={pick.id} className="flex items-center justify-between text-sm">
                          <span className="text-gray-500">#{pick.pick_number}</span>
                          <span className="font-medium truncate mx-2">{team?.team_name}</span>
                          <span className="text-gray-600">{pick.player?.name || '...'}</span>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </div>

            {/* Draft Board Mini */}
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <div className="p-4 border-b">
                <h3 className="font-semibold">Teams</h3>
              </div>
              <div className="p-4 space-y-3">
                {teams.map((team) => {
                  const teamPicks = picksByTeam[team.id] || [];
                  const isOnClock = team.id === draft.current_team_id;
                  
                  return (
                    <div 
                      key={team.id}
                      className={`p-2 rounded-lg ${isOnClock ? 'bg-blue-100 border border-blue-300' : 'bg-gray-50'}`}
                    >
                      <div className="flex items-center justify-between">
                        <span className={`font-medium text-sm ${isOnClock ? 'text-blue-700' : ''}`}>
                          {team.team_name}
                        </span>
                        <span className="text-xs text-gray-500">{teamPicks.length} picks</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DraftRoom;
