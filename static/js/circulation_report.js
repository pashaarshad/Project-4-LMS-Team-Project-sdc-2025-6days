document.addEventListener('DOMContentLoaded', function() {
    loadCirculationReport();
});

function loadCirculationReport() {
    fetch('/admin/fetch-circulation-data')
        .then(response => response.json())
        .then(data => {
            if (data.circulation) {
                const tableBody = document.getElementById('circulationTableBody');
                tableBody.innerHTML = '';

                data.circulation.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.issue_id}</td>
                        <td>${item.member_name}</td>
                        <td>${item.book_title}</td>
                        <td>${item.issue_date}</td>
                        <td>${item.due_date}</td>
                        <td>${item.return_date || '-'}</td>
                        <td><span class="status-badge ${item.current_status.toLowerCase()}">${item.current_status}</span></td>
                    `;
                    tableBody.appendChild(row);
                });
            }
        })
        .catch(error => console.error('Error loading circulation report:', error));
}
