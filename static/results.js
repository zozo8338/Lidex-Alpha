function vote(id, type) {
    fetch('/vote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: id, type: type }),
    }).then(response => response.json())
      .then(data => {
          console.log('Vote success:', data);
          location.reload();
      }).catch(error => console.error('Error:', error));
}
