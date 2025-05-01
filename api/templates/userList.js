function userListSuccess(data){
    const success = data.{{ const.FIELD_SUCCESS }};
    if (!success) return;
    for (user of data.{{ const.FIELD_DATA }}) {
        userListDiv.append(user.username + "  ");
    }
}

const userListDiv = document.querySelector(".userList");

function userListLoad() {
    fetch("{{ url_for('get_user_list') }}")
        .then((response) => response.json()).then(userListSuccess);
}

