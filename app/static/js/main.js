document.addEventListener('DOMContentLoaded', function() {
  // 闪现消息自动隐藏
  const alerts = document.querySelectorAll('.alert');
  if (alerts.length > 0) {
    alerts.forEach(alert => {
      setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => {
          alert.style.display = 'none';
        }, 500);
      }, 3000);
    });
  }

  // 表单验证
  const forms = document.querySelectorAll('form.needs-validation');
  if (forms.length > 0) {
    forms.forEach(form => {
      form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add('was-validated');
      });
    });
  }

  // 使用AJAX提交表单
  const ajaxForms = document.querySelectorAll('form.ajax-form');
  if (ajaxForms.length > 0) {
    ajaxForms.forEach(form => {
      form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // 获取表单数据
        const formData = new FormData(form);
        const formObject = {};
        formData.forEach((value, key) => {
          formObject[key] = value;
        });
        
        // 特殊处理标签字段（如果有）
        if (formObject.tags && typeof formObject.tags === 'string') {
          formObject.tags = formObject.tags.split(',').map(tag => tag.trim()).filter(tag => tag);
        }
        
        // 发送请求
        fetch(form.action, {
          method: form.method,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify(formObject)
        })
        .then(response => {
          if (!response.ok) {
            throw new Error('网络错误，请稍后重试');
          }
          return response.json();
        })
        .then(data => {
          showToast(data.message || '操作成功', 'success');
          
          // 处理成功后的操作，例如重定向
          if (form.dataset.redirect) {
            setTimeout(() => {
              window.location.href = form.dataset.redirect;
            }, 1000);
          }
        })
        .catch(error => {
          showToast(error.message || '发生错误，请稍后重试', 'danger');
        });
      });
    });
  }

  // 登录和注册功能
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', function(event) {
      event.preventDefault();
      
      const formData = new FormData(loginForm);
      const username = formData.get('username');
      const password = formData.get('password');
      
      fetch('/auth/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: username,
          password: password
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.access_token) {
          // 保存token
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          
          showToast('登录成功，正在跳转...', 'success');
          setTimeout(() => {
            window.location.href = '/debunk/articles';
          }, 1000);
        } else {
          showToast(data.message || '登录失败，请检查用户名和密码', 'danger');
        }
      })
      .catch(error => {
        showToast('登录过程中发生错误，请稍后重试', 'danger');
      });
    });
  }

  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', function(event) {
      event.preventDefault();
      
      const formData = new FormData(registerForm);
      const username = formData.get('username');
      const password = formData.get('password');
      const name = formData.get('name');
      const phone = formData.get('phone');
      
      fetch('/auth/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_name: username,
          password: password,
          name: name,
          phone: phone
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.message && data.message.includes('成功')) {
          showToast('注册成功，请登录', 'success');
          setTimeout(() => {
            window.location.href = '/auth/login';
          }, 1000);
        } else {
          showToast(data.message || '注册失败，请检查输入信息', 'danger');
        }
      })
      .catch(error => {
        showToast('注册过程中发生错误，请稍后重试', 'danger');
      });
    });
  }

  // 文章管理功能
  function loadArticles(page = 1, status = '', search = '') {
    const articleList = document.getElementById('article-list');
    if (!articleList) return;
    
    const url = `/api/debunk/articles?page=${page}&per_page=10${status ? '&status=' + status : ''}${search ? '&search=' + search : ''}`;
    
    fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.articles && data.articles.length > 0) {
        articleList.innerHTML = '';
        
        data.articles.forEach(article => {
          const statusClass = article.status === 'published' ? 'status-published' : 
                             article.status === 'draft' ? 'status-draft' : 'status-archived';
          
          const statusText = article.status === 'published' ? '已发布' : 
                            article.status === 'draft' ? '草稿' : '已归档';
          
          const tagsHtml = article.tags && article.tags.length > 0 ? 
            article.tags.map(tag => `<span class="article-tag">${tag}</span>`).join('') :
            '';
          
          const articleElement = document.createElement('div');
          articleElement.className = 'col-md-6 col-lg-4 mb-4';
          articleElement.innerHTML = `
            <div class="card article-card">
              <div class="card-body">
                <div class="article-header">
                  <h5><a href="/debunk/articles/${article.id}" class="article-title">${article.title}</a></h5>
                </div>
                <div class="article-meta">
                  <span>作者: ${article.author_id}</span>
                  <span>发布时间: ${article.published_at || article.created_at}</span>
                </div>
                <div class="article-tags">
                  ${tagsHtml}
                </div>
                <p class="article-summary">${article.summary || '无摘要'}</p>
                <div class="article-footer">
                  <span class="status-badge ${statusClass}">${statusText}</span>
                  <div>
                    <a href="/debunk/articles/${article.id}/edit" class="btn btn-sm btn-secondary">编辑</a>
                    <button class="btn btn-sm btn-danger delete-article" data-id="${article.id}">删除</button>
                  </div>
                </div>
              </div>
            </div>
          `;
          
          articleList.appendChild(articleElement);
        });
        
        // 添加分页
        const pagination = document.getElementById('pagination');
        if (pagination) {
          pagination.innerHTML = '';
          const totalPages = data.pages || 1;
          
          if (totalPages > 1) {
            for (let i = 1; i <= totalPages; i++) {
              const pageItem = document.createElement('li');
              pageItem.className = `page-item ${i === data.current_page ? 'active' : ''}`;
              pageItem.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
              pagination.appendChild(pageItem);
            }
            
            // 分页事件绑定
            const pageLinks = pagination.querySelectorAll('.page-link');
            pageLinks.forEach(link => {
              link.addEventListener('click', function(e) {
                e.preventDefault();
                const page = parseInt(this.dataset.page);
                const statusFilter = document.getElementById('status-filter');
                const searchInput = document.getElementById('search-input');
                
                loadArticles(
                  page, 
                  statusFilter ? statusFilter.value : '', 
                  searchInput ? searchInput.value : ''
                );
              });
            });
          }
        }
        
        // 删除文章事件绑定
        const deleteButtons = document.querySelectorAll('.delete-article');
        deleteButtons.forEach(button => {
          button.addEventListener('click', function() {
            const articleId = this.dataset.id;
            if (confirm('确定要删除这篇文章吗？此操作不可撤销！')) {
              deleteArticle(articleId);
            }
          });
        });
      } else {
        articleList.innerHTML = '<div class="col-12 text-center"><p>没有找到符合条件的文章</p></div>';
      }
    })
    .catch(error => {
      articleList.innerHTML = '<div class="col-12 text-center"><p>加载文章失败，请稍后重试</p></div>';
    });
  }
  
  // 加载文章列表
  const articleListPage = document.getElementById('article-list-page');
  if (articleListPage) {
    loadArticles();
    
    // 状态筛选
    const statusFilter = document.getElementById('status-filter');
    if (statusFilter) {
      statusFilter.addEventListener('change', function() {
        const searchInput = document.getElementById('search-input');
        loadArticles(1, this.value, searchInput ? searchInput.value : '');
      });
    }
    
    // 搜索功能
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
      searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const searchInput = document.getElementById('search-input');
        const statusFilter = document.getElementById('status-filter');
        loadArticles(1, statusFilter ? statusFilter.value : '', searchInput.value);
      });
    }
  }
  
  // 删除文章
  function deleteArticle(id) {
    fetch(`/api/debunk/articles/${id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.message && data.message.includes('删除')) {
        showToast('文章已成功删除', 'success');
        // 重新加载文章列表
        setTimeout(() => {
          loadArticles();
        }, 1000);
      } else {
        showToast(data.message || '删除失败，请稍后重试', 'danger');
      }
    })
    .catch(error => {
      showToast('删除过程中发生错误，请稍后重试', 'danger');
    });
  }
  
  // 文章表单提交（新建或编辑）
  const articleForm = document.getElementById('article-form');
  if (articleForm) {
    articleForm.addEventListener('submit', function(e) {
      e.preventDefault();
      
      const formData = new FormData(articleForm);
      const formObject = {};
      
      formData.forEach((value, key) => {
        formObject[key] = value;
      });
      
      // 处理标签
      if (formObject.tags) {
        formObject.tags = formObject.tags.split(',').map(tag => tag.trim()).filter(tag => tag);
      }
      
      // 处理关联报告，转换为数字数组
      if (formObject.rumor_reports) {
        formObject.rumor_reports = formObject.rumor_reports.split(',')
          .map(id => parseInt(id.trim()))
          .filter(id => !isNaN(id));
      }
      
      if (formObject.clarification_reports) {
        formObject.clarification_reports = formObject.clarification_reports.split(',')
          .map(id => parseInt(id.trim()))
          .filter(id => !isNaN(id));
      }
      
      const articleId = articleForm.dataset.id;
      const isEdit = !!articleId;
      
      const url = isEdit ? `/api/debunk/articles/${articleId}` : '/api/debunk/articles';
      const method = isEdit ? 'PUT' : 'POST';
      
      fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(formObject)
      })
      .then(response => response.json())
      .then(data => {
        if ((data.message && data.message.includes('成功')) || data.article_id) {
          showToast(isEdit ? '文章已成功更新' : '文章已成功发布', 'success');
          setTimeout(() => {
            window.location.href = '/debunk/articles';
          }, 1000);
        } else {
          showToast(data.message || '操作失败，请检查输入信息', 'danger');
        }
      })
      .catch(error => {
        showToast('操作过程中发生错误，请稍后重试', 'danger');
      });
    });
  }
});

// 显示提示消息
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `alert alert-${type} toast-message`;
  toast.innerHTML = message;
  
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.classList.add('show');
  }, 100);
  
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => {
      document.body.removeChild(toast);
    }, 500);
  }, 3000);
}

// 检查用户登录状态
function checkAuth() {
  const token = localStorage.getItem('access_token');
  if (!token) {
    window.location.href = '/auth/login';
    return false;
  }
  return true;
}

// 登出
function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  window.location.href = '/auth/login';
} 