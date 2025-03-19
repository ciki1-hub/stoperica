<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Session Viewer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        #searchBox {
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #ccc;
            border-radius: 5px;
            font-size: 16px;
        }
        #session-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); /* Adjust minmax for session card size */
            gap: 20px; /* Space between cards */
        }
        .session-card {
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 15px;
            background-color: #f9f9f9;
        }
        .session-card h3 {
            margin-top: 0;
        }
        .session-card p {
            margin: 5px 0;
        }
        .lap {
            margin-left: 20px;
        }
        .sector {
            margin-left: 40px;
        }
        #pagination {
            margin-top: 20px;
            text-align: center;
        }
        #pagination button {
            padding: 10px 20px;
            margin: 0 5px;
            border: 1px solid #ccc;
            border-radius: 5px;
            background-color: #f9f9f9;
            cursor: pointer;
        }
        #pagination button:disabled {
            background-color: #ddd;
            cursor: not-allowed;
        }
        #loading {
            text-align: center;
            margin: 20px 0;
            display: none;
        }
    </style>
</head>
<body>
    <h1>Session Viewer</h1>

    <!-- Search Box -->
    <input type="text" id="searchBox" placeholder="Search by username...">

    <!-- Session Grid -->
    <div id="session-grid">
        <!-- Session cards will be displayed here -->
    </div>

    <!-- Loading Spinner -->
    <div id="loading">Loading...</div>

    <!-- Pagination -->
    <div id="pagination">
        <button id="prevPage" disabled>Previous</button>
        <span id="pageInfo">Page 1 of 1</span>
        <button id="nextPage" disabled>Next</button>
    </div>

    <script>
        let currentPage = 1;
        let totalPages = 1;
        let searchTerm = '';
        const sessionsPerPage = 10; // Number of sessions per page

        // Fetch and display session data
        async function fetchSessions(page = 1, search = '') {
            showLoading(true);
            const response = await fetch(`/sessions?page=${page}&limit=${sessionsPerPage}&search=${search}`);
            const data = await response.json();
            showLoading(false);

            totalPages = data.totalPages;
            displaySessions(data.sessions);
            updatePagination();
        }

        // Display session data in a grid layout
        function displaySessions(sessions) {
            const sessionGrid = document.getElementById('session-grid');
            sessionGrid.innerHTML = ''; // Clear previous data

            if (sessions.length === 0) {
                sessionGrid.textContent = 'No sessions found.';
                return;
            }

            sessions.forEach(session => {
                const sessionCard = document.createElement('div');
                sessionCard.className = 'session-card';

                sessionCard.innerHTML = `
                    <h3>User ID: ${session.username}</h3>
                    <p><strong>Session:</strong> ${session.name}</p>
                    <p><strong>Date:</strong> ${session.date}</p>
                    <p><strong>Total Time:</strong> ${session.totalTime}</p>
                    <p><strong>Location:</strong> ${session.location}</p>
                    <p><strong>Fastest Lap:</strong> ${session.fastestLap}</p>
                    <p><strong>Slowest Lap:</strong> ${session.slowestLap}</p>
                    <p><strong>Average Lap:</strong> ${session.averageLap}</p>
                    <p><strong>Consistency:</strong> ${session.consistency}</p>
                `;

                // Display laps and sectors
                session.laps.forEach((lap, lapIndex) => {
                    const lapDiv = document.createElement('div');
                    lapDiv.className = 'lap';
                    lapDiv.innerHTML = `<strong>Lap ${lapIndex + 1}:</strong> ${lap}`;

                    // Display sectors for this lap
                    session.sectors[lapIndex].forEach((sector, sectorIndex) => {
                        const sectorDiv = document.createElement('div');
                        sectorDiv.className = 'sector';
                        sectorDiv.innerHTML = `<strong>Sector ${sectorIndex + 1}:</strong> ${sector}`;
                        lapDiv.appendChild(sectorDiv);
                    });

                    sessionCard.appendChild(lapDiv);
                });

                sessionGrid.appendChild(sessionCard);
            });
        }

        // Update pagination buttons and page info
        function updatePagination() {
            const prevPageButton = document.getElementById('prevPage');
            const nextPageButton = document.getElementById('nextPage');
            const pageInfo = document.getElementById('pageInfo');

            prevPageButton.disabled = currentPage <= 1;
            nextPageButton.disabled = currentPage >= totalPages;
            pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        }

        // Show or hide the loading spinner
        function showLoading(show) {
            const loadingDiv = document.getElementById('loading');
            loadingDiv.style.display = show ? 'block' : 'none';
        }

        // Add event listeners
        document.getElementById('searchBox').addEventListener('input', () => {
            searchTerm = document.getElementById('searchBox').value.trim();
            currentPage = 1; // Reset to the first page when searching
            fetchSessions(currentPage, searchTerm);
        });

        document.getElementById('prevPage').addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                fetchSessions(currentPage, searchTerm);
            }
        });

        document.getElementById('nextPage').addEventListener('click', () => {
            if (currentPage < totalPages) {
                currentPage++;
                fetchSessions(currentPage, searchTerm);
            }
        });

        // Fetch sessions when the page loads
        fetchSessions(currentPage, searchTerm);
    </script>
</body>
</html>
