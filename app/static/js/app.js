const bookForm = document.getElementById("book-form");
const booksTable = document.getElementById("books-table");
const message = document.getElementById("message");

async function loadBooks() {
    booksTable.replaceChildren();

    const loadingRow = document.createElement("tr");
    const loadingCell = document.createElement("td");
    loadingCell.colSpan = 4;
    loadingCell.textContent = "Loading books...";
    loadingRow.appendChild(loadingCell);
    booksTable.appendChild(loadingRow);

    try {
        const response = await fetch("/books");

        if (!response.ok) {
            throw new Error("Unable to fetch books.");
        }

        const data = await response.json();
        booksTable.replaceChildren();

        if (data.books.length === 0) {
            const row = document.createElement("tr");
            const cell = document.createElement("td");
            cell.colSpan = 4;
            cell.textContent = "No books available. Add your first book!";
            row.appendChild(cell);
            booksTable.appendChild(row);
            return;
        }

        data.books.forEach((book) => {
            const row = document.createElement("tr");

            const idCell = document.createElement("td");
            idCell.textContent = book.id;

            const nameCell = document.createElement("td");
            nameCell.textContent = book.name;

            const priceCell = document.createElement("td");
            priceCell.textContent = `₹${Number(book.price).toFixed(2)}`;

            const actionCell = document.createElement("td");
            const deleteButton = document.createElement("button");

            deleteButton.type = "button";
            deleteButton.textContent = "Delete";
            deleteButton.className = "delete-button";

            deleteButton.addEventListener("click", () => {
                deleteBook(book.id, deleteButton);
            });

            actionCell.appendChild(deleteButton);

            row.append(idCell, nameCell, priceCell, actionCell);
            booksTable.appendChild(row);
        });
    } catch (error) {
        booksTable.replaceChildren();

        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 4;
        cell.textContent = "Could not load books. Please try again.";
        row.appendChild(cell);
        booksTable.appendChild(row);

        console.error("Load books error:", error);
    }
}

bookForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const nameInput = document.getElementById("book-name");
    const priceInput = document.getElementById("book-price");
    const submitButton = bookForm.querySelector('button[type="submit"]');

    const name = nameInput.value.trim();
    const price = Number(priceInput.value);

    if (!name || !Number.isFinite(price) || price <= 0) {
        message.textContent = "Enter a valid book name and a price greater than zero.";
        return;
    }

    submitButton.disabled = true;
    message.textContent = "Adding book...";

    try {
        const response = await fetch("/books", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ name, price })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to add book.");
        }

        bookForm.reset();
        message.textContent = "Book added successfully!";

        await loadBooks();
    } catch (error) {
        message.textContent = error.message || "Something went wrong.";
        console.error("Add book error:", error);
    } finally {
        submitButton.disabled = false;
    }
});

async function deleteBook(bookId, button) {
    if (!confirm("Are you sure you want to delete this book?")) {
        return;
    }

    button.disabled = true;

    try {
        const response = await fetch(`/books/${bookId}`, {
            method: "DELETE"
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to delete book.");
        }

        message.textContent = "Book deleted successfully!";
        await loadBooks();
    } catch (error) {
        message.textContent = error.message || "Something went wrong.";
        console.error("Delete book error:", error);
        button.disabled = false;
    }
}

document.addEventListener("DOMContentLoaded", loadBooks);