
var configConfirmModal = new Vue({
    el: '#configConfirmModal',
    data: {
        show: false,
	    width: 500,
        msg: '',
        action: '',
        target: {},
        do: false,
        index: 0,
        type: 'app'
	},
    methods: {
        close: function() {
	        this.show=false;
	    },
	    commit: function() {
	        if(this.action=='del_antx'){
	            this.close()
	            this.$http.delete("{{url_for('antxProfile.project_antx')}}", {params:{'project_id': '{{project_id}}', 'env': this.target.env, 'app_id': this.target.app_id}, emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        config.load();
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
	        }else if(this.action=='del_diamond'){
	            this.close()
	            this.$http.delete("{{url_for('diamondProfile.project_diamond')}}", {params: {'project_id': '{{project_id}}', 'env': this.target.env, 'data_id': this.target.data_id}, emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        config.load();
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
	        }else if(this.action=='del_app_branch'){
	            this.close();
	            var env = []
	            for(i=0;i<config.antx_list.length;i++){
                    if(this.target.app_id==config.antx_list[i].app_id){
                        env.push(config.antx_list[i].env)
                     }
                }
	            this.$http.delete("{{url_for('appBranchProfile.project_app_branch')}}", {params: {'project_id': '{{project_id}}', 'app_id': this.target.app_id, 'version': this.target.version, 'antx_env': env.join(',')}, emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        app.load();
                        config.load();
                    }else{
                        errorModal.msg='删除失败';
                        errorModal.show=true;
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
	        }else if(this.action == 'recreate_app_branch'){
	            this.close();
	            this.$http.delete("{{url_for('appBranchProfile.project_app_branch')}}", {params: {'project_id': '{{project_id}}', 'app_id': this.target.app_id, 'version': this.target.version}, emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        if(this.type == 'app'){
                            var vcs_type  = app.app_branch_list[this.index].vcs_type
                            var app_name = app.app_branch_list[this.index].app_name
                            var app_type = app.app_branch_list[this.index].app_type
                            var vcs_full_url = app.app_branch_list[this.index].vcs_full_url
                        }else if (this.type != 'dzbd'){
                            var vcs_type  = app.share_branch_list[this.index].vcs_type
                            var app_name = app.share_branch_list[this.index].app_name
                            var app_type = app.share_branch_list[this.index].app_type
                            var vcs_full_url = app.share_branch_list[this.index].vcs_full_url
                        }else{
                            var vcs_type = dzbd.bd_list[0].vcs_type
                            var app_name = dzbd.bd_list[0].app_name
                            var app_type = dzbd.bd_list[0].app_type
                            var vcs_full_url = dzbd.bd_list[0].vcs_full_url
                        }
                        newAppModal.add(this.target.app_id, vcs_type, app_name, app_type, vcs_full_url)
                        app.load()
                    }else{
                        errorModal.msg='删除失败';
                        errorModal.show=true;
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
	        }else if(this.action == 'add_dzbd'){
	            this.close();
	            newAppModal.add({{config['DZBD_APP_ID']}}, 'svn', '{{config["DZBD_APP_NAME"]}}', 'dzbd', '{{config["DZBD_APP_VCS_FULL_URL"]}}')
	        }else if(this.action == 'sort_order'){
	            this.close()
	            var index = this.index
	            var order = this.target.order
	            var action = this.target.action
	            var flag = this.target.flag
	            if(flag == 0){
                    var idx = index + action
                    var new_order = order
                    var order = app.app_branch_list[idx].order
                    var app_id = app.app_branch_list[index].app_id
                    var version = app.app_branch_list[index].version
                    var f_type = app.app_branch_list[index].f_type

                    var new_app_id = app.app_branch_list[idx].app_id
                    var new_version = app.app_branch_list[idx].version
                    var new_f_type = app.app_branch_list[idx].f_type
                }else{
                    var idx = index + action
                    var new_order = order
                    var order = app.share_branch_list[idx].order
                    var app_id = app.share_branch_list[index].app_id
                    var version = app.share_branch_list[index].version
                    var f_type = app.share_branch_list[index].f_type

                    var new_app_id = app.share_branch_list[idx].app_id
                    var new_version = app.share_branch_list[idx].version
                    var new_f_type = app.share_branch_list[idx].f_type
                }
             app.edit_order(app_id, version, f_type, order)
             app.edit_order(new_app_id, new_version, new_f_type, new_order)
	        }
	    }
    }
});

var dzbd = new Vue({
    el: '#dzbd',
    data: {
        bd_list: [],
        code_review_status: 0,
        owner_id: '',
        developers: []
    },
    methods: {
        add: function(){
            configConfirmModal.action = 'add_dzbd'
            configConfirmModal.msg = '确认要新增电子保单配置吗?'
            configConfirmModal.show = true
        },
        recreate: function(version){
            app.recreate({{config['DZBD_APP_ID']}}, version, 0, 'dzbd')
        },
        del: function(version){
            app.del({{config['DZBD_APP_ID']}}, version)
        }
    }
});

var app = new Vue({
    el: '#app',
    data: {
        app_branch_list: [],
        code_review_status: 0,
        share_branch_list: [],
        owner_id: '',
        developers: []
    },
    methods: {
        edit: function(app_name, f_type, index, flag){
            editAppModal.app_name = app_name
            editAppModal.f_type = f_type
            editAppModal.index = index
            editAppModal.flag = flag
            editAppModal.show = true
        },
        recreate: function(app_id, version, index, type){
            configConfirmModal.action = 'recreate_app_branch'
            configConfirmModal.index = index
            configConfirmModal.type = type
            configConfirmModal.target = {'project_id': '{{project_id}}', 'app_id': app_id, 'version': version}
            configConfirmModal.msg = '确认要重新拉取分支吗?'
            configConfirmModal.show = true
        },
        del: function(app_id, version){
            configConfirmModal.action = 'del_app_branch'
            configConfirmModal.target = {'project_id': '{{project_id}}', 'app_id': app_id, 'version': version}
            configConfirmModal.msg = '确认要删除分支吗?'
            configConfirmModal.show = true
        },
        load: function(){
            this.$http.get("{{url_for('appBranchProfile.list_app_branch', project_id=project_id)}}", {emulateJSON: true}).then(
            function(response){
                //console.log();
                if(response.data.result == 1){
                    app.app_branch_list = [];
                    response.data.data.app.forEach(function(e){
                        app.app_branch_list.push(e)
                    });
                    app.share_branch_list = [];
                    response.data.data.share.forEach(function(e){
                        app.share_branch_list.push(e)
                    });
                    dzbd.bd_list = [];
                    response.data.data.dzbd.forEach(function(e){
                        dzbd.bd_list.push(e)
                    });
                }
            },function(res){
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
        },
        new_app_branch: function(){
            newAppModal.running = false;
            newAppModal.show = true;
            newAppModal.load_app_company()
        },
        sort: function(order,index,action,flag){
            configConfirmModal.show = true
            configConfirmModal.msg = '确定要改变应用分支排序吗？'
            configConfirmModal.target = {'order': order, 'action': action, 'flag': flag}
            configConfirmModal.index = index
            configConfirmModal.action = 'sort_order'
        },
        edit_order: function(app_id, version, f_type, order){
            this.$http.post("{{url_for('appBranchProfile.project_app_branch')}}", {"project_id": '{{project_id}}', "app_id": app_id, "version": version, "f_type": f_type, "order": order, "r":Math.random()}).then(
            function(response){
                if(response.data.result != 1){
                    errorModal.msg='更新失败';
                    errorModal.show=true;
                }else{
                    app.load();
                }
            },function(res){
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
        },
        review: function(app_id, branch, original, submit_test, review_token){
            if(original==submit_test){
                infoModal.msg = '初始版本和提测版本相同，无需Review';
                infoModal.show = true;
                return
            }
            this.$http.post("{{config['APPREPO_URL']}}/diff/request-diff", {"system": "duang", "project_id": "{{project_id}}", "app_id": app_id, "relative_path": "branch/"+branch, "origin_revision": original, "commit_revision": submit_test, "review_token": review_token}, {emulateJSON: true}).then(
            function(response){
                if(response.data.result == 1){
                    window.open('{{config['APPREPO_URL']}}/diff/' + response.data.data + '?review_token=' + encodeURIComponent(review_token), target='_blank')
                }else{
                    errorModal.msg = response.data.info;
                    errorModal.show = true;
                }
            },function(res){
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
        }
    },
    watch: {
        app_branch_list: function(val){
            newAntxModal.app_list = [];
            newAntxModal.app_list.push.apply(newAntxModal.app_list, app.app_branch_list);
            newAntxModal.app_list.push.apply(newAntxModal.app_list, app.share_branch_list);
        },
        share_branch_list: function(val){
            newAntxModal.app_list = [];
            newAntxModal.app_list.push.apply(newAntxModal.app_list, app.app_branch_list);
            newAntxModal.app_list.push.apply(newAntxModal.app_list, app.share_branch_list);
        }
    }
})

var config = new Vue({
    el: '#config',
    data: {
        antx_list: [],
        diamond_list: [],
        code_review_status: 0,
        owner_id: '',
        developers: [],
        view_ids: [],
        user_show: user_show,
        need_review: '',
    },
    methods: {
        load: function(){
            this.$http.get("{{url_for('antxProfile.list_antx', project_id=project_id)}}", {emulateJSON: true}).then(
            function(response){
                //console.log();
                if(response.data.result == 1){
                    config.antx_list = [];
                    response.data.data.forEach(function(e){
                        config.antx_list.push(e)
                    });
                    if(showAntxModal.code_review_open){
                        codeReviewDetailedModal.show_code_review()
                    }
                }
            },function(res){
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
            this.$http.get("{{url_for('diamondProfile.list_diamond', project_id=project_id)}}", {emulateJSON: true}).then(
            function(response){
                if(response.data.result == 1){
                    config.diamond_list = [];
                    response.data.data.forEach(function(e){
                        config.diamond_list.push(e)
                    });
                    if(showDiamondModal.code_review_open){
                        codeReviewDetailedModal.show_code_review()
                    }
                }
            },function(res){
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
        },
        new_antx: function(){
            newAntxModal.app_list = app.app_branch_list.concat(app.share_branch_list)
            newAntxModal.show = true;
            setTimeout(function(){
                for(i=0;i<config.antx_list.length;i++){
                    var app = config.antx_list[i].app_name
                    var env = config.antx_list[i].env
                    $('#'+app+'_'+env+'_env').attr('checked', 'checked')
                    $('#'+app+'_'+env+'_env').attr('disabled', 'disabled')
                }}, 100)
        },
        show_antx: function(app_id, env){
            showAntxModal.load(app_id, env);
            showAntxModal.need_review = config.need_review
            showAntxModal.code_review_open = false
            showAntxModal.show = true;
        },
        edit_antx: function(app_id, env){
            editAntxModal.load(app_id, env)
            editAntxModal.show = true;
        },
        del_antx: function(app_id, env){
            configConfirmModal.action = 'del_antx';
            configConfirmModal.target = {'app_id': app_id, 'env': env};
            configConfirmModal.msg = '确认要删除Antx配置吗?'
            configConfirmModal.show = true;
        },
        new_diamond: function(){
            newDiamondModal.data_id = ''
            newDiamondModal.env = 'test'
            newDiamondModal.m_type = 'after'
            newDiamondModal.content = ''
            newDiamondModal.base_content = ''
            newDiamondModal.base_version = ''
            newDiamondModal.checked = false
            newDiamondModal.mode = ''
            newDiamondModal.saved = false
            newDiamondModal.show = true
        },
        show_diamond: function(data_id, env){
            showDiamondModal.load(env, data_id)
            showDiamondModal.need_review = config.need_review
            showDiamondModal.code_review_open = false
            showDiamondModal.show = true
        },
        edit_diamond: function(data_id, env){
            editDiamondModal.load(env, data_id)
            editDiamondModal.show = true
        },
        del_diamond: function(data_id, env){
            configConfirmModal.action = 'del_diamond';
            configConfirmModal.target = {'data_id': data_id, 'env': env};
            configConfirmModal.msg = '确认要删除Diamond配置吗?'
            configConfirmModal.show = true;
        }
    }
});

var sqlreview = new Vue({
    el: '#sqlreview',
    data: {
        user_show: user_show,
        publish_status: 0,
        sql_list: {},
        developers: [],
        owner_id: '',
        code_review_status: 0,
        ready: {}
    },
    methods: {
        add_sql: function(){
            newSQLModal.show = true
            setTimeout(function(){
                $('#pre_before').attr('checked', 'checked')
                $('#prd_before').attr('checked', 'checked')
            }, 30)
        },
        edit_sql: function(){
            editSQLModal.show = true
            setTimeout(function(){
                for(var key in sqlreview.sql_list.sql_execution_config){
                    $("#edit_"+key+"_before").attr("checked", sqlreview.sql_list.sql_execution_config[key]["execution_before"])
                    $("#edit_"+key+"_after").attr("checked", sqlreview.sql_list.sql_execution_config[key]["execution_after"])
                }
            }, 30)
        },
        update_sql_review_status: function(env, status, manual){
            if(status=='pass'){
                sqlConfirmModal.msg = '确定通过吗？'
             }else{
                sqlConfirmModal.msg = ''
                sqlConfirmModal.show_remark = true
             }
            sqlConfirmModal.action = 'update_status'
            sqlConfirmModal.datas = {'env': env, 'status': status, 'manual': manual}
            sqlConfirmModal.show = true
        },
        sql_review: function(env){
            sqlConfirmModal.msg = '确定提交审核吗？'
            sqlConfirmModal.action = 'sql_review'
            sqlConfirmModal.datas = {'env': env}
            sqlConfirmModal.show = true
        },
        load_sql_review: function(){
            this.$http.get("{{url_for('projectProfile.list_sql_review', project_id=project_id)}}", {emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        sqlreview.sql_list = {};
                        if(response.data.data){
                            sqlreview.sql_list = response.data.data
                            sqlreview.sql_list['processing'] = {}
                            sqlreview.sql_list['processing']['pre'] = false
                            sqlreview.sql_list['processing']['prd'] = false
                         }
                         this.render_workflow('sql_ready')
                    }else{
                        sqlreview.sql_list = {};
                        errorModal.msg = response.data.message
                        errorModal.show=true;
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
            });
        },
        del_sql: function(){
            sqlConfirmModal.msg = "确定删除吗？"
            sqlConfirmModal.action = "del"
            sqlConfirmModal.show = true
        },
        disable_sql_execute: function(env){
            sqlConfirmModal.msg = "确定取消SQL执行吗？"
            sqlConfirmModal.action = "disable_execute"
            sqlConfirmModal.datas['env'] = env
            sqlConfirmModal.show = true
        },
        render_workflow: function(ready){
            if(ready == 'project_ready'){
                this.ready['project'] = true
            }else{
                this.ready['sql'] = true
            }
            if('status' in sqlreview.sql_list){
                var graphDefinition = "graph LR\nA(项目开始) -->|开发完成提交|B(Code Review)\nB-->|通过|C(测试中)\nC-->|通过|D(待申请发布)\nD-->|申请发布|E(发布中)\nE-->|成功|F(发布完成)\n"+
                                   "A(项目开始) -->|开发完成提交|G(预发 SQL Review)\nA(项目开始) -->|开发完成提交|H(生产 SQL Review)\n"+
                                   "G-->|通过|J(待预发执行)\nJ-->|执行|K(预发执行中)\nK-->|成功|L(预发执行结束)\n"+
                                   "H-->|通过|M(待生产执行)\nM-->|执行|N(生产执行中)\nN-->|成功|O(生产执行结束)\n"
                if(sqlreview.sql_list.status.pre == 'review'){
                    basic.sql_review_status = 1
                    graphDefinition += "style G fill:#F8EB16,stroke:#3333FF,stroke-width:2px\n";
                }
                if(sqlreview.sql_list.status.prd == 'review'){
                    basic.sql_review_status = 1
                    graphDefinition += "style H fill:#F8EB16,stroke:#3333FF,stroke-width:2px\n";
                }
                if(sqlreview.sql_list.status.pre == 'not_pass'){
                    graphDefinition += "style G fill:red,stroke:#3333FF,stroke-width:2px\n";
                }
                if(sqlreview.sql_list.status.prd == 'not_pass'){
                    graphDefinition += "style H fill:red,stroke:#3333FF,stroke-width:2px\n";
                }
                if(sqlreview.sql_list.status.pre == 'pass'){
                    graphDefinition += "style J fill:#F8EB16,stroke:#3333FF,stroke-width:2px\n";
                }
                if(sqlreview.sql_list.status.prd == 'pass'){
                    graphDefinition += "style M fill:#F8EB16,stroke:#3333FF,stroke-width:2px\n";
                }
                if(sqlreview.sql_list.status.pre == 'execute'){
                    basic.sql_review_status = 1
                    graphDefinition += "style K fill:#F8EB16,stroke:#3333FF,stroke-width:2px\n";
                }
                if(sqlreview.sql_list.status.prd == 'execute'){
                    basic.sql_review_status = 1
                    graphDefinition += "style N fill:#F8EB16,stroke:#3333FF,stroke-width:2px\n";
                }
                if(sqlreview.sql_list.status.pre == 'success'){
                    graphDefinition += "style L fill:#F8EB16,stroke:#3333FF,stroke-width:2px\n";
                }
                if(sqlreview.sql_list.status.prd == 'success'){
                    graphDefinition += "style O fill:#F8EB16,stroke:#3333FF,stroke-width:2px\n";
                }
                if(sqlreview.sql_list.status.pre == 'failed'){
                    graphDefinition += "style K fill:red,stroke:#3333FF,stroke-width:2px\n";
                }
                if(sqlreview.sql_list.status.prd == 'failed'){
                    graphDefinition += "style N fill:red,stroke:#3333FF,stroke-width:2px\n";
                }
            }else{
                var graphDefinition = "graph LR\nA(项目开始) -->|开发完成提交|B(Code Review)\nB-->|通过|C(测试中)\nC-->|通过|D(待申请发布)\nD-->|申请发布|E(发布中)\nE-->|成功|F(发布完成)\n"
            }
            if(basic.code_review_status==0){
                graphDefinition += "style A fill:#F8EB16,stroke:#3333FF,stroke-width:2px\n";
            }
            if(basic.code_review_status==1){
                graphDefinition += "style B fill:#F8EB16,stroke:#3333FF,stroke-width:2px\n";
            }
            if(basic.test_status==1){
                graphDefinition += "style C fill:#F8EB16,stroke:#3333FF,stroke-width:2px\n";
            }
            if(basic.test_status==2 && basic.publish_status==0){
                graphDefinition += "style D fill:#F8EB16,stroke:#3333FF,stroke-width:2px\n";
            }
            if(basic.publish_status==1){
                graphDefinition += "style E fill:#F8EB16,stroke:#3333FF,stroke-width:2px\n";
            }
            if(basic.publish_status==2){
                graphDefinition += "style F fill:#F8EB16,stroke:#3333FF,stroke-width:2px\n";
            }
         if(this.ready.project && this.ready.sql){
             var insertSvg = function(svgCode, bindFunctions){
                            $("#mermaid").html(svgCode);
                            };
             var graph = mermaidAPI.render('workflow', graphDefinition, insertSvg);
         }
    }
    }
});

var sqlConfirmModal = new Vue({
    el: '#sqlConfirmModal',
    data: {
        show: false,
        width: 500,
        msg: '',
        action: '',
        datas:{},
        show_remark: false,
        remark: '',
    },
    methods: {
        close:function () {
            this.show = false;
            this.msg = ''
        },
        commit:function () {
            this.show = false;
            this.msg = ''
            if(this.action=='del'){
                this.$http.post("{{url_for('projectProfile.del_sql_review', project_id=project_id)}}", {emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        infoModal.msg = "删除成功"
                        infoModal.show = true
                        sqlreview.load_sql_review()
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
            });
            }else if(this.action=='update_status'){
                if(this.datas.status == 'not_pass' && !this.remark){
                    infoModal.msg = '请填写审核不通过的原因'
                    infoModal.show = true
                }else{
                    data = sqlreview.sql_list
                    data['processing'][this.datas.env] = true
                    sqlreview.sql_list = {}
                    sqlreview.sql_list = data
                    this.$http.post("{{url_for('projectProfile.update_sql_review_status', project_id=project_id)}}", {"env": this.datas.env, "status": this.datas.status, "remark": this.remark, "manual": this.datas.manual}, {emulateJSON: true}).then(
                        function(response){
                            if(response.data.result == 1){
                                this.remark = ''
                                this.show_remark = false
                                window.location.reload()
                            }else{
                                this.remark = ''
                                this.show_remark = false
                                errorModal.msg = '更新失败,'+ response.data.message
                                errorModal.show=true;
                                data = sqlreview.sql_list
                                data['processing'][this.datas.env] = false
                                sqlreview.sql_list = {}
                                sqlreview.sql_list = data
                            }
                        },function(res){
                            errorModal.msg='网络连接异常，请稍后重试。';
                            errorModal.show=true;
                            this.remark = ''
                            this.show_remark = false
                            data = sqlreview.sql_list
                            data['processing'][this.datas.env] = false
                            sqlreview.sql_list = {}
                            sqlreview.sql_list = data
                    });
                }
            }else if (this.action=='sql_review'){
                data = sqlreview.sql_list
                data['processing'][this.datas.env] = true
                sqlreview.sql_list = {}
                sqlreview.sql_list = data

                $(basic.department_list).each(function (i,v) {
                    if(v.value == basic.selected_department){
                        dept_code = v.code;
                    }
                });
                this.$http.post("{{url_for('projectProfile.sql_review', project_id=project_id)}}", {"dept_code": dept_code, "env": this.datas.env}, {emulateJSON: true}).then(
                    function(response){
                        if(response.data.result == 1){
                            //sqlreview.load_sql_review()
                            window.location.reload()
                        }else{
                            if(response.data.error){
                                errorModal.msg = response.data.error
                            }else{
                                errorModal.msg = "提交失败"
                            }
                            data = sqlreview.sql_list
                            data['processing'][this.datas.env] = false
                            sqlreview.sql_list = {}
                            sqlreview.sql_list = data
                            errorModal.show=true;
                        }
                    },function(res){
                        errorModal.msg='网络连接异常，请稍后重试。';
                        errorModal.show=true;
                        data = sqlreview.sql_list
                        data['processing'][this.datas.env] = false
                        sqlreview.sql_list = {}
                        sqlreview.sql_list = data
                });
            }else if(this.action=='disable_execute'){
                this.$http.post("{{url_for('projectProfile.disable_sql_execute', project_id=project_id)}}", {"env": this.datas.env}, {emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        sqlreview.load_sql_review()
                        if(basic.publish_status){
                            infoModal.msg='SQL脚本状态更新为未提交，请至最新发布页点击取消执行按钮';
                        }else{
                            infoModal.msg='SQL脚本状态更新为未提交，项目发布后将不会执行SQL脚本';
                        }
                        infoModal.show=true;
                    }else{
                        errorModal.msg = "删除失败"
                        errorModal.show=true;
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
            }
         }
     }
});