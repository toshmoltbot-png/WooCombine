#!/usr/bin/env python3
"""
Refactor EventSetup.jsx to remove CSV upload logic and integrate ImportResultsModal.
"""

import re

def refactor_eventsetup():
    input_file = "frontend/src/components/EventSetup.jsx"
    output_file = "frontend/src/components/EventSetup_NEW.jsx"
    
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Step 1: Update imports - remove CSV utils, add ImportResultsModal
    content = re.sub(
        r"import \{ Upload,.*?\} from 'lucide-react';",
        "import { Upload, UserPlus, RefreshCcw, Users, Copy, Link2, QrCode, Edit, Hash, ArrowLeft, FileText } from 'lucide-react';",
        content
    )
    
    content = re.sub(
        r"import \{ autoAssignPlayerNumbers \} from.*?\n",
        "",
        content
    )
    
    content = re.sub(
        r"import \{ parseCsv,.*?OPTIONAL_HEADERS \} from.*?\n",
        "",
        content
    )
    
    content = content.replace(
        'import EditEventModal from "./EditEventModal";',
        'import EditEventModal from "./EditEventModal";\nimport ImportResultsModal from "./Players/ImportResultsModal";'
    )
    
    # Step 2: Remove SAMPLE_ROWS constant
    content = re.sub(
        r"const SAMPLE_ROWS = \[.*?\];",
        "",
        content,
        flags=re.DOTALL
    )
    
    # Step 3: Remove CSV-related state variables (keep manual player form state)
    # Find the state section and rebuild it
    state_pattern = r"(// Reset tool state.*?)(// CSV upload state.*?)(// Manual add player state)"
    def replace_state(match):
        return match.group(1) + "\n\n  // Import modal state (replaces CSV upload state)\n  const [showImportModal, setShowImportModal] = useState(false);\n\n  " + match.group(3)
    
    content = re.sub(state_pattern, replace_state, content, flags=re.DOTALL)
    
    # Step 4: Remove drag-and-drop and drill schema state
    content = re.sub(
        r"  // Drill definitions from event schema.*?const fileInputRef = useRef\(\);",
        "",
        content,
        flags=re.DOTALL
    )
    
    # Step 5: Remove all CSV-related functions but keep manual add functions
    # This is complex, so we'll use line-based filtering
    
    # Step 6: Replace the massive Player Upload Section (Step 3)
    new_player_section = '''        {/* Step 3: Add Players Section - STREAMLINED VERSION */}
        <div id="player-upload-section" className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-3">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 bg-brand-primary text-white rounded-full flex items-center justify-center text-sm font-bold">3</div>
            <h2 className="text-lg font-semibold text-gray-900">Add Players</h2>
          </div>
          
          {/* Player Count Status */}
          {playerCountLoading ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4 text-center">
              <p className="text-gray-600">Loading player count...</p>
            </div>
          ) : (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <div className="flex items-center gap-3">
                <Users className="w-5 h-5 text-blue-600" />
                <div>
                  <p className="text-blue-900 font-semibold">
                    {playerCount === 0 ? 'No players yet' : `${playerCount} ${playerCount === 1 ? 'player' : 'players'} in roster`}
                  </p>
                  <p className="text-blue-700 text-sm">
                    {playerCount === 0 ? 'Add players using the options below' : 'Add more players or manage your roster on the Players page'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Primary Actions - Grid */}
          <div className="grid grid-cols-2 gap-3 mb-6">
            {/* Import from File - PRIMARY METHOD */}
            <button
              onClick={() => setShowImportModal(true)}
              className="bg-brand-primary hover:bg-brand-secondary text-white font-semibold px-6 py-4 rounded-xl transition flex flex-col items-center justify-center gap-2 shadow-sm"
              type="button"
            >
              <FileText className="w-6 h-6" />
              <span>Import Players from File</span>
              <span className="text-xs opacity-90">CSV or Excel</span>
            </button>
            
            {/* Manual Add - SECONDARY METHOD */}
            <button
              onClick={() => {
                const newState = !showManualForm;
                setShowManualForm(newState);
                if (newState && manualFormRef.current) {
                  setTimeout(() => {
                    manualFormRef.current.scrollIntoView({ 
                      behavior: 'smooth', 
                      block: 'start' 
                    });
                  }, 100);
                }
              }}
              className="bg-white hover:bg-gray-50 text-gray-900 font-semibold px-6 py-4 rounded-xl transition flex flex-col items-center justify-center gap-2 shadow-sm border-2 border-gray-200"
              type="button"
            >
              <UserPlus className="w-6 h-6" />
              <span>Add Player Manually</span>
              <span className="text-xs text-gray-600">One at a time</span>
            </button>
          </div>

          {/* Manual Add Player Form */}
          {showManualForm && (
            <div ref={manualFormRef} className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <h3 className="font-semibold text-gray-900 mb-3">Add Single Player</h3>
              <form onSubmit={handleManualSubmit} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    name="first_name"
                    placeholder="First Name *"
                    value={manualPlayer.first_name}
                    onChange={handleManualChange}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-primary"
                    required
                  />
                  <input
                    type="text"
                    name="last_name"
                    placeholder="Last Name *"
                    value={manualPlayer.last_name}
                    onChange={handleManualChange}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-primary"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    name="number"
                    placeholder="Jersey # (optional)"
                    value={manualPlayer.number}
                    onChange={handleManualChange}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-primary"
                  />
                  <input
                    type="text"
                    name="age_group"
                    placeholder="Age Group (optional)"
                    value={manualPlayer.age_group}
                    onChange={handleManualChange}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-primary"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    type="submit"
                    disabled={manualStatus === 'loading'}
                    className="flex-1 bg-brand-primary hover:bg-brand-secondary disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium px-4 py-2 rounded-lg transition"
                  >
                    {manualStatus === 'loading' ? 'Adding...' : 'Add Player'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowManualForm(false);
                      setManualPlayer({ first_name: '', last_name: '', number: '', age_group: '' });
                      setManualStatus('idle');
                      setManualMsg('');
                    }}
                    className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition"
                  >
                    Cancel
                  </button>
                </div>
                
                {/* Success/Error Messages */}
                {manualStatus === 'success' && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-green-800 text-sm">
                    ✅ {manualMsg}
                  </div>
                )}
                {manualStatus === 'error' && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-800 text-sm">
                    ❌ {manualMsg}
                  </div>
                )}
              </form>
            </div>
          )}

          {/* Help Text */}
          <div className="text-sm text-gray-600 text-center mt-4">
            <p><strong>Tip:</strong> For bulk uploads, use "Import Players from File" to add multiple players at once.</p>
            <p className="mt-1">View and manage your roster on the <Link to="/players" className="text-brand-primary hover:underline font-medium">Players page</Link>.</p>
          </div>
        </div>
'''
    
    # Replace Step 3 section (from "Step 3: Add Players Section" to "Step 4: Invite Coaches & Share")
    player_section_pattern = r"(\s+){/\* Step 3: Add Players Section \*/}.*?(\s+){/\* Step 4: Invite Coaches & Share \*/}"
    content = re.sub(player_section_pattern, "\n" + new_player_section + "\n\n        {/* Step 4: Invite Coaches & Share */}", content, flags=re.DOTALL)
    
    # Write output
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Refactored EventSetup.jsx -> {output_file}")
    print("Review the changes, then:")
    print(f"  mv {output_file} {input_file}")

if __name__ == "__main__":
    refactor_eventsetup()

