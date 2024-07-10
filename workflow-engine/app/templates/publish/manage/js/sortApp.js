    var sortConfirmModal = new Vue({
        el: '#sortConfirmModal',
        data: {
            show: false,
            width: 500,
            msg: '',
            action: '',
            target: {},
            index: 0,
            type: 'app'
        },
        methods: {
            close: function() {
                this.show=false;
            },
            commit: function() {
                this.close()
	            var index = this.index
	            var order = this.target.order
	            var action = this.target.action
	            var flag = this.target.flag
	            if(flag == 0){
                    var idx = index + action
                    var new_order = order
                    var order = sortAppModal.app_branch_list[idx].order
                    var app_id = sortAppModal.app_branch_list[index].app_id
                    var version = sortAppModal.app_branch_list[index].version
                    var f_type = sortAppModal.app_branch_list[index].f_type

                    var new_app_id = sortAppModal.app_branch_list[idx].app_id
                    var new_version = sortAppModal.app_branch_list[idx].version
                    var new_f_type = sortAppModal.app_branch_list[idx].f_type
                }else{
                    var idx = index + action
                    var new_order = order
                    var order = sortAppModal.share_branch_list[idx].order
                    var app_id = sortAppModal.share_branch_list[index].app_id
                    var version = sortAppModal.share_branch_list[index].version
                    var f_type = sortAppModal.share_branch_list[index].f_type

                    var new_app_id = sortAppModal.share_branch_list[idx].app_id
                    var new_version = sortAppModal.share_branch_list[idx].version
                    var new_f_type = sortAppModal.share_branch_list[idx].f_type
                }
                sortAppModal.edit_order(app_id, version, f_type, order)
                sortAppModal.edit_order(new_app_id, new_version, new_f_type, new_order)
            }
        }
    });

    var sortAppModal = new Vue({
        el: '#sortAppModal',
        data: {
            show: false,
            app_branch_list: [],
            share_branch_list: [],
            project_id: '',
            publish_id: '',
            edit_success: 0,
        },
        methods: {
            close: function(){
                this.show = false
            },
            load: function(){
                this.$http.get("{{config['SERVER_URL']}}/app-branch/list/"+this.project_id, {emulateJSON: true}).then(
                function(response){
                    //console.log();
                    if(response.data.result == 1){
                        sortAppModal.app_branch_list = [];
                        response.data.data.app.forEach(function(e){
                            sortAppModal.app_branch_list.push(e)
                        });
                        sortAppModal.share_branch_list = [];
                        response.data.data.share.forEach(function(e){
                            sortAppModal.share_branch_list.push(e)
                        });
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
            },
            sort: function(order,index,action,flag){
                sortConfirmModal.show = true
                sortConfirmModal.msg = '确定要改变应用分支排序吗？'
                sortConfirmModal.target = {'order': order, 'action': action, 'flag': flag}
                sortConfirmModal.index = index
            },
            edit_order: function(app_id, version, f_type, order){
                this.$http.post("{{url_for('appBranchProfile.project_app_branch')}}", {"project_id": this.project_id, "app_id": app_id, "version": version, "f_type": f_type, "order": order, "r":Math.random()}).then(
                function(response){
                    if(response.data.result != 1){
                        errorModal.msg='更新失败';
                        errorModal.show=true;
                    }else{
                        this.edit_success += 1;
                        if(this.edit_success>=2){
                            this.sort_publish_order();
                        }
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
            },
            sort_publish_order: function(){
                this.$http.post("{{url_for('publishProfile.app_sort')}}", {"project_id": this.project_id, "publish_id": this.publish_id, "r":Math.random()}).then(
                function(response){
                    if(response.data.result != 1){
                        errorModal.msg='更新失败';
                        errorModal.show=true;
                    }else{
                        sortAppModal.load();
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
            }
        }
    });