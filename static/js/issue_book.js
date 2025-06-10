document.addEventListener('DOMContentLoaded', function() {
    loadMembers();
    loadBooks();
});

function loadMembers() {
    fetch('/admin/get-available-members')
        .then(response => response.json())
        .then(data => {
            const memberSelect = document.getElementById('memberSelect');
            memberSelect.innerHTML = '<option value="">Select Member</option>';
            
            data.members.forEach(member => {
                memberSelect.innerHTML += `
                    <option value="${member.id}">${member.fullname} (${member.email})</option>
                `;
            });
        })
        .catch(error => console.error('Error loading members:', error));
}

function loadBooks() {
    fetch('/admin/get-available-books')
        .then(response => response.json())
        .then(data => {
            const bookSelect = document.getElementById('bookSelect');
            bookSelect.innerHTML = '<option value="">Select Book</option>';
            
            data.books.forEach(book => {
                bookSelect.innerHTML += `
                    <option value="${book.book_id}">${book.title} by ${book.author}</option>
                `;
            });
        })
        .catch(error => console.error('Error loading books:', error));
}

function issueBook() {
    const memberId = document.getElementById('memberSelect').value;
    const bookId = document.getElementById('bookSelect').value;
    const dueDays = document.getElementById('dueDays').value;

    if (!memberId || !bookId || !dueDays) {
        alert('Please fill all fields');
        return;
    }

    fetch('/admin/issue-book', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_id: memberId,
            book_id: bookId,
            due_days: dueDays
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Book issued successfully!');
            location.reload();
        } else {
            alert(data.error || 'Failed to issue book');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to issue book');
    });
}
