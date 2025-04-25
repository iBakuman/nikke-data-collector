from collector.tournament_recorder import TournamentRecorder, MatchPhase

def test_tournament_recorder(tournament_recorder: TournamentRecorder):
    tournament_recorder.record_tournament("testdata/tournament", MatchPhase.QUARTERFINALS, [1])
