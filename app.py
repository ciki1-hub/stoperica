@app.route('/sessions', methods=['GET'])
def get_sessions():
    # Format sessions as plain text
    formatted_sessions = []
    for session in sessions:
        formatted_session = f"""
Session: {session.get('name', 'N/A')}
Date: {session.get('date', 'N/A')}
Total Time: {session.get('totalTime', 'N/A')}
Location: {session.get('location', 'N/A')}
Fastest Lap: {session.get('fastestLap', 'N/A')}
Slowest Lap: {session.get('slowestLap', 'N/A')}
Average Lap: {session.get('averageLap', 'N/A')}
Consistency: {session.get('consistency', 'N/A')}

"""
        # Add laps and sectors
        for i, lap in enumerate(session.get('laps', [])):
            formatted_session += f"Lap {i + 1}: {lap}\n"
            sectors = session.get('sectors', [])
            if i < len(sectors):
                for sector in sectors[i]:
                    formatted_session += f"   {sector}\n"  # Use the prefixed sector string directly
            formatted_session += "\n"

        formatted_sessions.append(formatted_session)

    return "\n".join(formatted_sessions), 200, {'Content-Type': 'text/plain'}
