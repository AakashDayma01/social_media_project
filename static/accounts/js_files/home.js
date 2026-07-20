const currentUser = document.body.dataset.currentUser;

document.addEventListener("DOMContentLoaded", () => {
    const feedContainer = document.getElementById("infinite-feed-container");
    const endTrigger = document.getElementById("feed-end-trigger");
    let loading = false;
    const originalPosts = $(".insta-card");
    const observer = new IntersectionObserver((entries)=>{
        if(!entries[0].isIntersecting || loading){
            return;
        }
        loading = true;
        originalPosts.each(function(){
            const clonedPost = $(this).clone(true);
            let oldId = clonedPost.attr("id");
            if(oldId){
                clonedPost.attr(
                    "id",
                    oldId + "-clone-" + Date.now()
                );
            }
            $(endTrigger).before(clonedPost);
        });
        loading = false;
    },{
        rootMargin:"300px",
        threshold:0
    });
    observer.observe(endTrigger);
});

document.addEventListener("click", function(e){
    const likeBtn = e.target.closest(".like-btn");
    const deleteBtn=e.target.closest(".delete-btn");
    const followBtn = e.target.closest(".follow-btn");
    const commentBtn = e.target.closest(".open-comments-btn");

    if(likeBtn){
        handleLike(likeBtn);
    }else if(deleteBtn){
        handleDelete(deleteBtn);
    }else if(followBtn){
        handleFollow(followBtn)
    }else if (commentBtn){
        openCommentsPopup(commentBtn);
    }
});


function handleLike(button){
    const postId = button.dataset.postId;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    fetch(`/post/like-post/${postId}/`, {
        method: "POST",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            'X-CSRFToken': csrfToken 
        }
    })
    .then(response => response.json())
    .then(data => {
        const likeButtons = document.querySelectorAll(`button.like-btn-icon[data-post-id="${postId}"]`);
        if(data.liked){
            likeButtons.forEach(btn => btn.innerHTML = "❤️");
        }else{
            likeButtons.forEach(btn => btn.innerHTML = "🤍");
        }
        document.querySelectorAll(`.likes-count-${postId}`).forEach(element => {element.innerHTML = `${data.total_likes} likes`;});
    })
    .catch(error => {
        console.log(error);
    });
}

function handleDelete(button){
    const postId = button.dataset.postId;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    let confirmation = confirm("Do you want to delete this post?");
    if(!confirmation){
        return;
    }
    fetch(`/post/delete-post/${postId}/`, {
        method: "POST",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            'X-CSRFToken': csrfToken 
        }
    })
    .then(response => response.json())
    .then(data => {
        if(data.success){
            document.getElementById(`post-${postId}`).remove();
        }
        else{
            alert("Unable to delete the post.");
        }
    })
    .catch(error => {console.log(error);});
}


function handleFollow(button){
    const targetUserId = button.dataset.id; 
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const formData = new FormData();
    formData.append('id', targetUserId);

    fetch('/user/toggle-follow/', {
        method: "POST",
        body: formData,
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            'X-CSRFToken': csrfToken 
        }
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success'){
            document.querySelectorAll(`.follow-btn[data-id="${targetUserId}"]`).forEach(btn => {
                if(data.action === 'follow'){
                    btn.textContent = 'Unfollow';
                } else {
                    btn.textContent = 'Follow';
                }
            });
            document.querySelectorAll(`.follower-count-val[data-id="${targetUserId}"]`).forEach(el => {
            el.textContent = data.follower_count;
            });
        } else {
            alert(data.message || "An error occurred.");
        }
    })
    .catch(error => {
        console.log("Error handling follow relationship: ", error);
    });
}


document.addEventListener("DOMContentLoaded", function () {
    const commentButtons = document.querySelectorAll(".open-comments-btn");
    const modalBody = document.getElementById("modalCommentsBody");
    modalBody.addEventListener('click', function (event) {
        const button = event.target.closest('.reply-btn');
        const edit_button = event.target.closest('.edit-btn');
        const delete_button = event.target.closest('.delete-comment-btn');
        const like_button = event.target.closest('.like-comment-btn');
        const parentComment = event.target.closest('.reply-block , .comment-block');
        let childComments = ""
        if (button) {
            const commentId = button.dataset.id;
            const username = button.dataset.user;
            document.getElementById('parentCommentInput').value = commentId;
            document.getElementById('replyingTo').innerHTML = `Replying to @${username}`;
            document.getElementById('commentText').focus();
        }
        else if (edit_button) {
            if (edit_button.dataset.user !== currentUser) {
                alert("You can only edit your own comments.");
                return;
            }else{
                const commentId = edit_button.dataset.id;
                const username = edit_button.dataset.user;
                const commentContentElement = edit_button.closest('.comment-block, .reply-block').querySelector('p');
                const commentContent = commentContentElement ? commentContentElement.textContent : '';
                document.getElementById('parentCommentInput').value = commentId;
                document.getElementById('replyingTo').innerHTML = `Editing comment by @${username}`;
                document.getElementById('commentText').value = commentContent;
                document.getElementById('commentText').focus();
            }
        }
        else if (delete_button){
            const postId = document.getElementById("postIdInput").value;
            if (delete_button.dataset.user !== currentUser) {
                alert("You can only delete your own comments.");
                return;
            }else{
                const commentId = delete_button.dataset.id;
                let confirmation = confirm("Do you want to delete this comment?");
                if(!confirmation){
                    return;
                }
                fetch(`/post/comments/${postId}/delete/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                        "X-Requested-With": "XMLHttpRequest",
                        "Content-Type": "application/x-www-form-urlencoded",
                        },
                        body: new URLSearchParams({
                            comment_id: commentId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if(data.success){
                        const commentElement = document.getElementById(`comment-${commentId}`);
                         if(commentElement){
                            const textElement = commentElement.querySelector('p');
                            if (textElement) textElement.textContent = data.content;

                            const authorElement = commentElement.querySelector('strong');
                            if (authorElement) authorElement.textContent = "@deleted";

                            const timeElement = commentElement.querySelector('small');
                            if (timeElement) timeElement.textContent = data.timestamp;

                            const editBtn = commentElement.querySelector('.edit-btn');
                            const deleteBtn = commentElement.querySelector('.delete-comment-btn');
                            if (editBtn) editBtn.remove();
                            if (deleteBtn) deleteBtn.remove();

                        }
                    }else{
                        alert(data.error || "Failed to delete the comment.");
                    }
                })
                .catch(error => {
                    console.log(error);
                    alert("An error occurred while trying to delete the comment.");
                });
            }
        }
        else if (like_button){
            const commentId = like_button.dataset.id;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            fetch(`/post/like-comment/${commentId}/`, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    'X-CSRFToken': csrfToken 
                }
            })
            .then(response => response.json())
            .then(data => {
                if(data.liked){
                    like_button.innerHTML = "❤️";
                }else{
                    like_button.innerHTML = "🤍";
                }
                document.getElementById(`likes-count-${commentId}`).innerHTML = `${data.total_likes} likes`;
            })
            .catch(error => {
                console.log(error);
            });
        }else{
            const elementId = parentComment.id.replace("comment-", "");
            const repliesContainer = document.getElementById(`replies-container-${elementId}`);

            if (repliesContainer) {
                const replyCount = repliesContainer.querySelectorAll('.reply-block').length;
                if (repliesContainer.style.display === "none" || repliesContainer.style.display === "") {
                    repliesContainer.style.display = "block"; 
                } else {
                    repliesContainer.style.display = "none";  
                    document.getElementById(`comments-count-${elementId}`).textContent = `${replyCount}` > 0 ? `${replyCount} replies` : '';
                }
            }
        }
    });
    
});

function generateCommentHtml(comment, isReply=false) {
    function getTotalRepliesCount(comment) {
        let count = 0;
        if (comment.replies) {
            comment.replies.forEach(reply => {
                count += 1 + getTotalRepliesCount(reply);
            });
        }
        return count;
    }

    let editButton = "";
    if (comment.username === currentUser && !comment.is_deleted) {
        editButton = `
            <button class="btn btn-sm btn-link edit-btn" data-id="${comment.id}" data-user="${comment.username}">
                Edit
            </button>
            <button class="btn btn-sm btn-link delete-comment-btn" data-id="${comment.id}" data-user="${comment.username}">
                Delete
            </button>
        `;
    }
    const totalReplies = getTotalRepliesCount(comment);
    const replyCountText = totalReplies > 0 ? `${totalReplies} replies` : '';
    let heartIcon = comment.liked_by_user ? "❤️" : "🤍";
    let userName = comment.is_deleted ? "@deleted" : `@${comment.username}`;
    let htmlContent = `
        <div class="${isReply ? 'reply-block' : 'comment-block'} mb-3 border-bottom pb-2" id="comment-${comment.id}">
            <div class="d-flex justify-content-between">
                <strong class="text-dark">${userName}</strong>
                <small class="text-muted">${comment.timestamp}</small>
            </div>
            <p class="mb-1 mt-1 text-dark" >${comment.content}</p>
            <button type="button" class="like-comment-btn btn btn-sm " data-id="${comment.id}">
                ${heartIcon}
            </button>
            <span id="likes-count-${comment.id}" class="text-secondary">
                ${comment.total_likes} likes
            </span>
            <button class="btn btn-sm btn-link reply-btn" data-id="${comment.id}" data-user="${comment.username}">
                Reply
            </button>
            ${editButton}
            <small class="text-muted" id="comments-count-${comment.id}">${replyCountText}</small>
                                        
            <div id="replies-container-${comment.id}" class="replies-section ms-4 ps-2 border-start text-secondary" style="display: none;">
    `;
    comment.replies.forEach(reply => {
        htmlContent += generateCommentHtml(reply, true);
    });
    htmlContent += `
            </div>
        </div>
    `;
    return htmlContent;

}

function openCommentsPopup(button){
    const commentsModal = new bootstrap.Modal(document.getElementById("commentsModal"));
    const modalBody = document.getElementById("modalCommentsBody");
    document.getElementById("postIdInput").value = button.dataset.postId;
    document.getElementById("parentCommentInput").value = "";
    document.getElementById("replyingTo").innerHTML = "";
    document.getElementById("commentText").value = "";
    const url = button.getAttribute("data-url");
    modalBody.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div></div>';
    commentsModal.show();
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.comments.length > 0) {
                let htmlContent = '';
                data.comments.forEach(comment => {
                    htmlContent += generateCommentHtml(comment);
                });
                modalBody.innerHTML = htmlContent;
            } else {
                modalBody.innerHTML = '<p class="text-muted text-center">No comments yet.</p>';
            }
        })
        .catch(error => {
            modalBody.innerHTML = '<p class="text-danger text-center">Failed to load comments.</p>';
            console.error("Error payload structure mapping error:", error);
        });
}

document.getElementById("commentForm").addEventListener("submit", function(e){
    e.preventDefault();
    const postId = document.getElementById("postIdInput").value;
    const parent = document.getElementById("parentCommentInput").value;
    const content = document.getElementById("commentText").value.trim();
    const modalBody = document.getElementById("modalCommentsBody");
    const formType = document.getElementById("replyingTo").innerHTML.includes("Editing") ? "edit" : "add";
    if(content === ""){
        alert("Please write a comment.");
        return;
    }
    fetch(`/post/comments/${postId}/${formType}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            content: content,
            parent: parent
        })
    })
    .then(response => response.json())
    .then(data => {
        if(data.success){
            if(data.parent_id){
                const repliesContainer = document.getElementById(`replies-container-${data.parent_id}`);
                if(repliesContainer){
                    let heartIcon = data.liked_by_user ? "❤️" : "🤍";
                    repliesContainer.style.display = "block";
                    repliesContainer.insertAdjacentHTML('beforeend', `
                        <div class="reply-block py-1 mt-2 bg-light p-2 rounded" id="comment-${data.id}">
                            <div class="d-flex justify-content-between">
                                <strong class="text-dark">@${data.username}</strong>
                                <small class="text-muted" style="font-size: 0.8rem;">${data.timestamp}</small>
                            </div>
                            <p class="mb-0 text-dark">${data.content}</p>
                            <button type="button" class="like-comment-btn btn btn-sm " data-id="${data.id}">
                                ${heartIcon}
                            </button>
                            <span id="likes-count-${data.id}" class="text-secondary">
                                ${data.total_likes} likes
                            </span>
                            <button class="btn btn-sm btn-link reply-btn" data-id="${data.id}" data-user="${data.username}">
                                Reply
                            </button>
                            <button class="btn btn-sm btn-link edit-btn" data-id="${data.id}" data-user="${data.username}">
                                Edit
                            </button>
                            <button class="btn btn-sm btn-link delete-comment-btn" data-id="${data.id}" data-user="${data.username}">
                                Delete
                            </button>
                            <div id="replies-container-${data.id}" class="replies-section ms-4 ps-2 border-start text-secondary"></div>
                        </div>
                    `);
                }
                
            }else{
                if (data.type === "edit"){
                    document.getElementById(`comment-${data.id}`).querySelector('p').textContent = data.content;
                    document.getElementById(`comment-${data.id}`).querySelector('small').textContent = data.timestamp;
                }else{
                    let heartIcon = data.liked_by_user ? "❤️" : "🤍";
                    modalBody.insertAdjacentHTML('beforeend', `
                        <div class="comment-block mb-3 border-bottom pb-2" id="comment-${data.id}">
                            <div class="d-flex justify-content-between">
                                <strong text-dark>@${data.username}</strong>
                                <small class="text-muted">${data.timestamp}</small>
                            </div>
                            <p class="mb-1 mt-1 text-dark" >${data.content}</p>
                            <button type="button" class="like-comment-btn btn btn-sm " data-id="${data.id}">
                                ${heartIcon}
                            </button>
                            <span id="likes-count-${data.id}" class="text-secondary">
                                ${data.total_likes} likes
                            </span>
                            <button class="btn btn-sm btn-link reply-btn" data-id="${data.id}" data-user="${data.username}">
                                Reply
                            </button>
                            <button class="btn btn-sm btn-link edit-btn" data-id="${data.id}" data-user="${data.username}">
                                Edit
                            </button>    
                            <button class="btn btn-sm btn-link delete-comment-btn" data-id="${data.id}" data-user="${data.username}">
                                Delete
                            </button>                              
                            <div id="replies-container-${data.id}" class="replies-section ms-4 ps-2 border-start text-secondary"></div>
                        </div>
                    `);
                }
            }
            document.getElementById("commentText").value = "";
            document.getElementById("parentCommentInput").value = "";
            document.getElementById("replyingTo").innerHTML = "";
        }else{
            alert(data.error);
        }   
    })
    .catch(error => {
        console.log(error);
    });
});
