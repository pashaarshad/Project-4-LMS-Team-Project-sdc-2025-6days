document.addEventListener('DOMContentLoaded', function() {
    loadReports();

    // Add search functionality
    document.getElementById('report-search').addEventListener('input', function(e) {
        filterReports(e.target.value.toLowerCase());
    });
});

function loadReports() {
    fetch('/admin/get-reports')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('reports-table-body');
            tableBody.innerHTML = '';
            
            data.reports.forEach(report => {
                const row = document.createElement('tr');
                const returnDate = report.return_date ? new Date(report.return_date).toLocaleDateString() : '-';
                const status = report.return_date ? 'Completed' : 'Borrowed';
                const daysOverdue = report.days_overdue > 0 ? report.days_overdue : 0;
                
                row.innerHTML = `
                    <td>${report.issue_id}</td>
                    <td>${report.user_name}</td>
                    <td>${report.book_title}</td>
                    <td>${new Date(report.issue_date).toLocaleDateString()}</td>
                    <td>${new Date(report.due_date).toLocaleDateString()}</td>
                    <td>${returnDate}</td>
                    <td>${daysOverdue}</td>
                    <td><span class="status-badge ${status.toLowerCase()}">${status}</span></td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error loading reports:', error));
}

function filterReports(searchTerm) {
    const rows = document.getElementById('reports-table-body').getElementsByTagName('tr');
    
    for (let row of rows) {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    }
}

function exportReportToExcel() {
    window.location.href = '/admin/export-reports';
}

function returnBook(issueId) {
    if (confirm('Are you sure you want to return this book?')) {
        fetch(`/admin/return-book/${issueId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Book returned successfully!');
                loadReports(); // Reload the reports table
            } else {
                alert(data.error || 'Failed to return book');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to return book');
        });
    }
}
