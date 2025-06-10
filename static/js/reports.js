document.addEventListener('DOMContentLoaded', function() {
    loadReports();

    // Add search functionality
    document.getElementById('report-search').addEventListener('input', function(e) {
        filterReports(e.target.value.toLowerCase());
    });
});
// okok
function loadReports() {
    fetch('/admin/get-reports')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('reports-table-body');
            tableBody.innerHTML = '';
            
            data.reports.forEach(report => {
                const row = document.createElement('tr');
                row.setAttribute('data-issue-id', report.issue_id);
                
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
                    <td>
                        ${!report.return_date ? 
                            `<button onclick="returnBook(${report.issue_id})" class="return-btn">Return Book</button>` :
                            `<button class="return-btn completed" disabled>Returned</button>`
                        }
                    </td>
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
                // Update the UI to show the book as returned
                const row = document.querySelector(`tr[data-issue-id="${issueId}"]`);
                if (row) {
                    // Update status badge
                    const statusCell = row.querySelector('td:nth-last-child(2)');
                    if (statusCell) {
                        statusCell.innerHTML = '<span class="status-badge completed">Completed</span>';
                    }
                    
                    // Update return date
                    const returnDateCell = row.querySelector('td:nth-child(6)');
                    if (returnDateCell) {
                        returnDateCell.textContent = new Date().toLocaleDateString();
                    }
                    
                    // Disable return button
                    const actionCell = row.querySelector('td:last-child');
                    if (actionCell) {
                        actionCell.innerHTML = '<button class="return-btn completed" disabled>Returned</button>';
                    }
                }
                
                alert('Book returned successfully!');
                // Optionally reload the entire table
                loadReports();
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
