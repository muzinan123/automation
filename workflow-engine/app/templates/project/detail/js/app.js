
var editAppModal = new Vue({
    el: '#editAppModal',
    data: {
        show: false,
	    width: 500,
        app_name: '',
        f_type: '',
        index: 0,
        flag: 0
    },
    methods: {
        close: function(){
            this.show = false
        },
        edit: function(){
            if(this.flag == 0){
                var app_id  = app.app_branch_list[this.index].app_id
                var version = app.app_branch_list[this.index].version
                var order = app.app_branch_list[this.index].order
            }else{
                var app_id  = app.share_branch_list[this.index].app_id
                var version = app.share_branch_list[this.index].version
                var order = app.share_branch_list[this.index].order
            }
            this.$http.post("{{url_for('appBranchProfile.project_app_branch')}}", {"project_id": '{{project_id}}', "app_id": app_id, "version": version, "f_type": this.f_type, "order": order, "r":Math.random()}).then(
            function(response){
                if(response.data.result == 1){
                    app.load()
                    this.show = false
                }else{
                    errorModal.msg='保存失败';
                    errorModal.show=true;
                }
            },function(res){
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
        }
    }
});

var newAppModal = new Vue({
    el: '#newAppModal',
    data: {
        show: false,
	    width: 1300,
        selected_company: '',
        selected_department: '',
        selected_production: '',
        selected_project: '',
        company_list: [],
        department_list: [],
        production_list: [],
        project_list: [],
        query: '',
        rc_list: [],
        running: false,
    },
    watch: {
        selected_company: function(val){
            if(val){
                this.load_app_department();
            }
        },
        selected_department: function(val){
            if(val){
                this.selected_production = ''
                this.production_list = []
                this.load_app_production();
             }
        }
    },
    methods: {
        close: function(event) {
            this.show = false;
            this.query = ''
            this.project_list = []
            this.company_list = []
            this.department_list = []
            this.production_liat = []
            this.selected_company = ''
            this.selected_department = ''
            this.selected_production = ''
        },
        ok: function() {
            if(!this.selected_project){
                this.show=false;
                errorModal.msg='请选择应用。';
                errorModal.show=true;
            }
            datas = []
            project = this.project_list[this.selected_project]
            data = {
                'app_id': project.id,
                'app_name': project.name,
            }
            datas.push(data)
            add_app(datas);
            this.show=false;
        },
        load_app_company: function() {
            this.$http.get("{{config['APPREPO_URL']}}/api/app/company/list", {params: {"r":Math.random()}, emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        this.company_list = []
                        this.company_list = response.data.data.companyList
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
        },
        load_app_department: function() {
            this.$http.get("{{config['APPREPO_URL']}}/api/app/department/list", {params: {"company_id":this.selected_company, "r":Math.random()}, emulateJSON: true}).then(
                function(response){
                    this.department_list = []
                    if(response.data.result == 1){                                ;
                        this.department_list = response.data.data.departmentList
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
         },
        load_app_production: function() {
            this.$http.get("{{config['APPREPO_URL']}}/api/app/production/list", {params: {"company_id":this.selected_company, "department_id":this.selected_department, "r":Math.random()}, emulateJSON: true}).then(
            function(response){
                if(response.data.result == 1){                                ;
                    this.production_list = response.data.data.productionList
                }
            },function(res){
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
        },
        load_app_project: function() {
            this.$http.get("{{config['APPREPO_URL']}}/api/app/project/list", {params: {"company_id":this.selected_company, "department_id":this.selected_department, "production_id":this.selected_production, "r":Math.random()}, emulateJSON: true}).then(
            function(response){
                if(response.data.result == 1){
                    newAppModal.project_list = []
                    response.data.data.projectList.forEach(function(e){
                        if(e.is_micro=='N' && e.language=='JAVA' && e.vcs_type=='svn'){
                            e['is_exist'] = false
                            e['version'] = 0
                            e['index'] = 0
                            if(e.type == 'app'){
                                len = app.app_branch_list.length
                                for(i=0; i < app.app_branch_list.length; i++){
                                    if(e.id == app.app_branch_list[i].app_id){
                                        e['is_exist'] = true
                                        e['version'] =  app.app_branch_list[i].version
                                        e['index'] = i
                                        newAppModal.rc_list.push(e)
                                        break;
                                    }
                                }
                            }else{
                                len = app.share_branch_list.length
                                for(i=0; i < app.share_branch_list.length; i++){
                                    if(e.name == app.share_branch_list[i].app_name){
                                        e['is_exist'] = true
                                        e['version'] =  app.share_branch_list[i].version
                                        e['index'] = i
                                        newAppModal.rc_list.push(e)
                                        break;
                                    }
                                }
                            }
                            newAppModal.project_list.push(e)
                        }
                    })
                }
            },function(res){
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
        },
        filter: function(){
            if (this.selected_company && this.selected_department && this.selected_production){
                this.load_app_project()
            }
        },
        filterByName: function(){
            var new_list = []
            var projects = []
            if(this.query && this.query.length <3){
                    errorModal.msg='查询内容长度至少为3个字符';
                    errorModal.show=true;
            }else if(this.query){
                this.$http.get("{{config['APPREPO_URL']}}/api/app/project/query", {params: {"query": this.query}, emulateJSON: true}).then(
                    function(response){
                        if(response.data.result == 1){
                            newAppModal.project_list = []
                            response.data.data.projectList.forEach(function(e){
                                if(e.is_micro=='N' && e.language=='JAVA' && e.vcs_type=='svn'){
                                    e['is_exist'] = false
                                    e['version'] = 0
                                    e['index'] = 0
                                    if(e.type == 'app'){
                                        len = app.app_branch_list.length
                                        for(i=0; i < app.app_branch_list.length; i++){
                                            if(e.id == app.app_branch_list[i].app_id){
                                                e['is_exist'] = true
                                                e['version'] =  app.app_branch_list[i].version
                                                e['index'] = i
                                                newAppModal.rc_list.push(e)
                                                break;
                                            }
                                        }
                                    }else{
                                        len = app.share_branch_list.length
                                        for(i=0; i < app.share_branch_list.length; i++){
                                            if(e.name == app.share_branch_list[i].app_name){
                                                e['is_exist'] = true
                                                e['version'] =  app.share_branch_list[i].version
                                                e['index'] = i
                                                newAppModal.rc_list.push(e)
                                                break;
                                            }
                                        }
                                    }
                                    newAppModal.project_list.push(e)
                                }
                            })
                        }
                    },function(res){
                        errorModal.msg='网络连接异常，请稍后重试。';
                        errorModal.show=true;
                });
            }
        },
        add: function(app_id, vcs_type, app_name, app_type, vcs_full_url){
            this.running = true;
            this.$http.put("{{url_for('appBranchProfile.project_app_branch')}}", {"project_id": '{{project_id}}', "app_id": app_id, "vcs_type": vcs_type, "app_name": app_name, "app_type": app_type, "vcs_full_url": vcs_full_url}).then(
            function(response){
                this.running = false;
                if(response.data.result == 1){
                    app.load()
                    newAppModal.filterByName()
                }else{
                    errorModal.msg='添加失败';
                    errorModal.show=true;
                    this.close()
                }
            },function(res){
                this.running = false;
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
        },
        recreate: function(app_id, version, index, type){
            this.running = true;
            app.recreate(app_id, version, index, type)
            this.show = false
        }
    }
});
