var basic = new Vue({
    el: '#tab1',
    data: {
        name:'',
        alias: '',
        selected_company: '',
        selected_department: '',
        selected_production: '',
        selected_system: '',
        type: '',
        owner_id: '',
        owner: {},
        ba_id: '',
        app_system_id: '',
        sql_script_url:'',
        summary: '',
        code_review:[],
        qa: [],
        developer: [],
        company_list: [],
        department_list: [],
        production_list: [],
        system_list: [],
        ba_list: [],
        qa_list: [],
        code_review_list: [],
        dev_list: [],
        demand_review_status: '',
        code_review_status: '',
        sql_review_status: '',
        data_review_status: '',
        test_status: '',
        publish_status: '',
        jira_issue_key: '',
        user_show: user_show,
        chosen_ready: false,
        all_ready: false,
        record: false,
        graphDefinition: '',
        jira_project_key: '',
        jira_version_id: '',
        regulator_id: '',
    },
    watch:{
        selected_company:function (val) {
            if(val){
                this.load_app_department();
            }
        },
        selected_department: function (val) {
            if(val){
                this.production_id = [];
                this.system_list = [];
                this.load_app_production();
                this.load_system_list();
            }

        }
    },
    methods:{
        verify_inputs: function(){
            if(!(this.name && this.selected_company && this.selected_department && this.selected_production
                && this.type && $("#begin_date").val() && $("#publish_date").val() && this.owner_id && this.ba_id
                && this.qa.length && this.developer.length && this.code_review.length)){
                return false;
            }
            return true;
        },
        update: function(){
            if(this.verify_inputs()){
                var company_code = '';
                var company_label = '';
                var dept_code = '';
                var dept_label = '';
                var product_code = '';
                var product_label = '';
                $(basic.company_list).each(function (i,v) {
                    if(v.value == basic.selected_company){
                        company_code = v.code;
                        company_label = v.label;
                    }
                });
                $(basic.department_list).each(function (i,v) {
                   if(v.value == basic.selected_department){
                       dept_code = v.code;
                       dept_label = v.label;
                   }
                });
                $(basic.production_list).each(function (i,v) {
                    if(v.value == basic.selected_production){
                        product_code = v.code;
                        product_label = v.label;
                    }
                });
                this.$http.post("{{url_for('projectProfile.update', project_id=project_id)}}",{"r":Math.random(), "name": this.name,
                    "alias": this.alias, "company_id": this.selected_company, "company_code": company_code, "company_label": company_label,
                    "dept_id": this.selected_department, "dept_code": dept_code, "dept_label": dept_label, "app_system_id": this.selected_system,
                "product_id": this.selected_production, 'product_code': product_code, 'product_label': product_label,"type": this.type, "begin_date": $("#begin_date").val(), "expect_publish_date": $("#publish_date").val(),
                "owner_id": this.owner_id, "ba_id": this.ba_id, "sql_script_url": this.sql_script_url, "qa": this.qa.join(','), "developer": this.developer.join(','),
                    "code_review": this.code_review.join(','),"summary": this.summary},{emulateJSON: true}).then(
                    function (response) {
                        if(response.data.success == 1){
                            infoModal.msg = '更新成功';
                            infoModal.show = true;
                            window.location.reload()
                        }else{
                            errorModal.msg = '更新失败';
                            errorModal.show = true;
                        }
                    },function (res) {
                        errorModal.msg='网络连接异常，请稍后重试。';
                        errorModal.show=true;
                    }
                )
            }else{
                errorModal.show = true;
                errorModal.msg = '项目基础信息中有必填项未填写!';
            }
        },
        del:function () {
            basicConfirmModal.msg = "确认删除吗?";
            basicConfirmModal.action = "del";
            basicConfirmModal.show = true;
        },
        submit:function () {
            //owner提交
            if(!basic.verify_inputs()){
                errorModal.msg='项目基础信息中有必填项未填写!';
                errorModal.show=true;
                return false;
            }
            if(!test.verify_inputs()){
                errorModal.msg='提交测试页中有必填项未填写!';
                errorModal.show=true;
                return false;
            }
            if(app.app_branch_list.length == 0 && app.share_branch_list.length == 0){
                verifyConfirmModal.msg = '你没有拉取代码分支, 确认提交Review吗?';
            }
            sql_review_flag = false
            if('status' in sqlreview.sql_list){
                for(var key in sqlreview.sql_list.status){
                    if(sqlreview.sql_list.status[key] == 'init' && key != 'aut'){
                        sql_review_flag = true
                        break
                    }
                }
            }
            if(sql_review_flag){
                verifyConfirmModal.msg = "项目将被提交并进行SQL Review, 确认提交Review吗?";
             }else{
                verifyConfirmModal.msg = "项目将被提交, 但不会进行SQL Review, 确认提交Review吗?";
             }
            verifyConfirmModal.type = "project";
            verifyConfirmModal.action = "submit";
            verifyConfirmModal.show = true;
        },
        rollback:function () {
            //项目撤回
            verifyConfirmModal.msg = "确认撤回项目吗?";
            verifyConfirmModal.type = "project";
            verifyConfirmModal.action = "rollback";
            verifyConfirmModal.show = true;
        },
        load_app_company: function() {
            this.$http.get("{{config['APPREPO_URL']}}/api/app/company/list", {params: {"r":Math.random()}, emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        this.company_list = [];
                        this.company_list = response.data.data.companyList;
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
        },
        load_app_department: function() {
            this.$http.get("{{config['APPREPO_URL']}}/api/app/department/list", {params: {"company_id":this.selected_company, "r":Math.random()}, emulateJSON: true}).then(
                function(response){
                    this.department_list = [];
                    if(response.data.result == 1){
                        this.department_list = response.data.data.departmentList;
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
         },
        load_app_production: function() {
            this.$http.get("{{config['APPREPO_URL']}}/api/app/production/list", {params: {"company_id":this.selected_company, "department_id":this.selected_department, "r":Math.random()}, emulateJSON: true}).then(
            function(response){
                if(response.data.result == 1){
                    this.production_list = response.data.data.productionList;
                }
            },function(res){
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
        },
        load_system_list: function() {
            this.$http.get("{{config['APPREPO_URL']}}/api/app/system/list", {params: {"company_id":this.selected_company, "department_id":this.selected_department, "r":Math.random()}, emulateJSON: true}).then(
            function(response){
                if(response.data.result == 1){
                    this.system_list = response.data.data.systemList;
                }
            },function(res){
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
        },
        apply_publish: function(){
            basic.department_list.forEach(function(e){
                if(e.value==basic.selected_department){
                    publishModal.dept_code = e.code;
                }
            });
            publishModal.issue_id = this.regulator_id
            publishModal.type = this.type
            publishModal.show = true
            now = new Date()
            now_date = formatDate(now)
            setTimeout(function(){
                        $('#scheduled_time').datetimepicker({format: 'YYYY-MM-DD HH:mm'});
                        $('#scheduled_time').data('DateTimePicker').minDate(now_date)
                        $('#scheduled_time').val('')
                        }, 500)
        },
        load_project:function () {
            this.$http.get("{{url_for('projectProfile.detail_basic', project_id=project_id)}}",{"r":Math.random()},{emulateJSON: true}).then(
                function (response) {
                    if(response.data.result == 1){
                        this.name = response.data.data.name;
                        this.alias = response.data.data.alias;
                        this.type = response.data.data.type;
                        this.selected_company = response.data.data.company_id;
                        this.selected_production = response.data.data.product_id;
                        this.selected_department = response.data.data.dept_id;
                        this.selected_system = response.data.data.system_id;
                        $("#begin_date").val(response.data.data.begin_date);
                        $("#publish_date").val(response.data.data.expect_publish_date);
                        this.owner_id = response.data.data.owner_id;
                        this.owner = response.data.data.owner;
                        this.ba_id = response.data.data.ba_id;
                        this.sql_script_url = response.data.data.sql_script_url;
                        this.summary = response.data.data.summary;
                        this.demand_review_status = response.data.data.demand_review_status;
                        this.code_review_status = response.data.data.code_review_status;
                        this.data_review_status = response.data.data.data_review_status;
                        this.test_status = response.data.data.test_status;
                        this.publish_status = response.data.data.publish_status;
                        this.jira_project_key = response.data.data.jira_project_key
                        this.jira_version_id = response.data.data.jira_version_id
                        this.regulator_id = response.data.data.regulator_id
                        $(response.data.data.dev_list).each(function(i, v){
                            basic.developer.push(v.id);
                            config.view_ids.push(v.id)
                        });
                        $(response.data.data.code_review_list).each(function (i, v) {
                            basic.code_review.push(v.id);
                            config.view_ids.push(v.id)
                        });
                        $(response.data.data.qa_list).each(function (i, v) {
                            basic.qa.push(v.id);
                            config.view_ids.push(v.id)
                        });
                        this.jira_issue_key = response.data.data.jira_issue_key;
                        app.developers = basic.developer
                        app.owner_id = basic.owner_id
                        app.code_review_status = basic.code_review_status

                        dzbd.developers = basic.developer
                        dzbd.owner_id = basic.owner_id
                        dzbd.code_review_status = basic.code_review_status


                        config.developers = basic.developer
                        config.owner_id = basic.owner_id
                        config.code_review_status = basic.code_review_status
                        config.view_ids.push(basic.owner_id)
                        config.view_ids.push(basic.ba_id)
                        if({{config['CONFIG_CODE_REVIEW_LIMIT_DEPT_ID']}}.indexOf(basic.selected_department) > -1 && this.code_review_status == 1){
                            config.need_review = true
                        }

                        sqlreview.developers = basic.developer
                        sqlreview.owner_id = basic.owner_id
                        sqlreview.code_review_status = basic.code_review_status
                        sqlreview.publish_status = basic.publish_status

                        test.load_test()

                        if(this.code_review_status > 0  || '{{session['userId']}}' != this.owner_id){
                            $('input').attr('disabled','disabled')
                            $('textarea').attr('disabled','disabled')
                            $('#company').attr('disabled', 'disabled')
                            $('#department').attr('disabled', 'disabled')
                            $('#product_module').attr('disabled', 'disabled')
                            $('#system').attr('disabled', 'disabled')
                            $('#project_type').attr('disabled', 'disabled')
                            $('#Owner').attr('disabled', 'disabled')
                            $('#BA').attr('disabled', 'disabled')
                            if(this.code_review_status > 1 || '{{session['userId']}}' != this.owner_id){
                                $('#qa').attr('disabled', 'disabled')
                                $('#developer').attr('disabled', 'disabled')
                                $('#code_review').attr('disabled', 'disabled')
                            }
                        }
                        if(this.user_show['pe'] == 2 && this.code_review_status>0 && this.publish_status == 0){
                            $("#project_type").removeAttr('disabled')
                        }

                        if(this.publish_status==2){
                            this.graphDefinition += "style F fill:#F8EB16,stroke:#3333FF,stroke-width:2px\n";
                        }

                        if(basic.verify_inputs() && test.verify_inputs()){
                            basic.all_ready=true;
                        }
                        sqlreview.render_workflow('project_ready')
                    }else{
                        errorModal.msg='项目不存在';
                        errorModal.show=true;
                        window.location.href="{{url_for('projectProfile.project')}}"
                    }
            },function (res) {
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            })
        },
        go_jira:function () {
            if(this.jira_issue_key){
                window.open("{{config['JIRA_SERVER_URL']}}/browse/" + this.jira_issue_key);
            }else if(this.jira_version_id){
                window.open("{{config['JIRA_SERVER_URL']}}/projects/"+ this.jira_project_key+"/versions/" + this.jira_version_id);
            }
        },
        approve:function (action, type) {
            if(type == 'code_review'){
                codeReviewDetailedModal.status_ok = true
                codeReviewDetailedModal.action = action
                if(action=="pass"){
                    codeReviewDetailedModal.msg='以上是Code Review的记录，确认Code Review通过吗?'
                }else{
                    codeReviewDetailedModal.msg='以上是Code Review的记录，确认Code Review不通过吗?'
                }
                codeReviewDetailedModal.show_code_review()
            }else{
                if(type == 'test_verify'){
                    if(action == 'pass'){
                        verifyConfirmModal.msg = '确认测试验证通过?';
                    }else if(action == 'reject'){
                        verifyConfirmModal.msg = '确认测试验证不通过?';
                    }
                }else{
                    if(action == 'pass'){
                        verifyConfirmModal.msg = '确认' + type + '通过?';
                    }else if(action == 'reject'){
                        verifyConfirmModal.msg = '确认' + type + '不通过?';
                    }
                }
                verifyConfirmModal.show = true;
            }
            verifyConfirmModal.action = action;
            verifyConfirmModal.type = type;
        },
        load_ba_list:function () {
            this.$http.get("{{url_for('baseProfile.get_user_by_privilege', privilege='ba')}}",{"r":Math.random()},{emulateJSON: true}).then(
                function (response) {
                    this.ba_list = response.data;
                    this.init_chosen();
                }
            )
        },
        load_qa_list:function () {
            this.$http.get("{{url_for('baseProfile.get_user_by_privilege', privilege='qa')}}",{"r":Math.random()},{emulateJSON: true}).then(
                function (response) {
                    this.qa_list = response.data;
                    this.init_chosen();
                }
            )
        },
        load_code_review_list:function () {
            this.$http.get("{{url_for('baseProfile.get_user_by_privilege', privilege='code_review')}}",{"r":Math.random()},{emulateJSON: true}).then(
                function (response) {
                    this.code_review_list = response.data;
                    this.init_chosen();
                }
            )
        },
        load_dev_list:function () {
            this.$http.get("{{url_for('baseProfile.get_user_by_privilege', privilege='dev')}}",{"r":Math.random()},{emulateJSON: true}).then(
                function (response) {
                    this.dev_list = response.data;
                    this.init_chosen();
                }
            )
        },
        init_chosen:function(){
            if(this.qa_list.length>0 && this.code_review_list.length>0 && this.dev_list.length>0){
                setTimeout(function(){
                    $('.chosen-select').chosen({
                        search_contains: true
                    });
                    basic.chosen_ready = true;
                }, 100);
            }
        }
    }
});

var verifyConfirmModal = new Vue({
    el: '#verifyConfirmModal',
    data: {
        show: false,
        width: 500,
        msg: '',
        action: '',
        type: ''
    },
    methods: {
        close:function () {
            this.show = false;
        },
        commit:function () {
            this.show = false;
            var submit_pass = true
            var form = new FormData()
            action = this.type + "_" + this.action
            form.append('action', action)
            form.append('operator_id', '{{session['userId']}}')
            if(this.action == 'submit'){
                if(!basic.verify_inputs()){
                    submit_pass = false
                }else{
                    var company_code = '';
                    var company_label = '';
                    var dept_code = '';
                    var dept_label = '';
                    var product_code = '';
                    var product_label = '';
                    $(basic.company_list).each(function (i,v) {
                        if(v.value == basic.selected_company){
                            company_code = v.code;
                            company_label = v.label;
                        }
                    });
                    $(basic.department_list).each(function (i,v) {
                       if(v.value == basic.selected_department){
                           dept_code = v.code;
                           dept_label = v.label;
                       }
                    });
                    $(basic.production_list).each(function (i,v) {
                        if(v.value == basic.selected_production){
                            product_code = v.code;
                            product_label = v.label;
                        }
                    });
                    form.append('name', basic.name)
                    form.append('alias', basic.alias)
                    form.append('company_id', basic.selected_company)
                    form.append('company_code', company_code)
                    form.append('company_label', company_label)
                    form.append('dept_id', basic.selected_department)
                    form.append('dept_code', dept_code)
                    form.append('dept_label', dept_label)
                    form.append('app_system_id', basic.selected_system)
                    form.append('product_id', basic.selected_production)
                    form.append('product_code', product_code)
                    form.append('product_label', product_label)
                    form.append('type', basic.type)
                    form.append('begin_date', $("#begin_date").val())
                    form.append('expect_publish_date', $("#publish_date").val())
                    form.append('owner_id', basic.owner_id)
                    form.append('ba_id', basic.ba_id)
                    form.append('sql_script_url', basic.sql_script_url)
                    form.append('qa', $("#qa").val().join(","))
                    form.append('developer', $("#developer").val().join(","))
                    form.append('code_review', $("#code_review").val().join(","))
                    form.append('summary', basic.summary)
                }
            }
            if(submit_pass){
                $.AMUI.progress.start();
                jQuery.ajax({
                    url: "{{url_for('projectProfile.approve', project_id=project_id)}}",
                    data: form,
                    cache: false,
                    type: "POST",
                    // 告诉jQuery不要去处理发送的数据
                    processData : false,
                    // 告诉jQuery不要去设置Content-Type请求头
                    contentType : false,
                    timeout : 20000,
                    success: function(response) {
                        $.AMUI.progress.done();
                        console.log(response);
                        if(response.success == 1){
                            verifyConfirmModal.reset()
                            if(response.message){
                                infoModal.msg = '操作成功<br>'+response.message
                                infoModal.show = true;
                                setTimeout(function(){
                                    window.location.reload();
                                }, 3000)
                            }else{
                                infoModal.msg = '操作成功';
                                infoModal.show = true;
                                window.location.reload();
                            }
                        }else{
                            errorModal.msg = "提交失败, "+response.message;
                            errorModal.show = true;
                            verifyConfirmModal.reset()
                            setTimeout(function(){
                                    window.location.reload();
                            }, 3000)
                        }
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        errorModal.msg='网络连接异常，请稍后重试。';
                        errorModal.show=true;
                        verifyConfirmModal.reset()
                    }
                });
            }else{
                errorModal.show = true;
                errorModal.msg = '项目基础信息中有必填项未填写!';
                verifyConfirmModal.reset()
            }
        },
        reset: function(){
            this.msg = ''
            this.action = ''
            this.type = ''
        }
    }
});

var basicConfirmModal = new Vue({
    el: '#basicConfirmModal',
    data: {
        show: false,
        width: 500,
        msg: '',
        action: '',
        datas: {}
    },
    methods: {
        close:function () {
            this.show = false;
        },
        commit:function () {
            this.show = false;
            if(this.action=='del'){
                //删除
                this.$http.post("{{url_for('projectProfile.delete', project_id=project_id)}}").then(
                    function (response) {
                        if(response.data.result == 1){
                            infoModal.msg = '删除成功';
                            infoModal.show = true;
                            window.location.href="{{url_for('projectProfile.project')}}";
                        }else{
                            errorModal.msg = '删除失败';
                            errorModal.show = true;
                        }
                    },function (res) {
                        errorModal.msg='网络连接异常，请稍后重试。';
                        errorModal.show=true;
                    }
                )
            }else if(this.action=='apply_publish'){
                spinningModal.msg='执行中...';
                spinningModal.show=true;
                $.AMUI.progress.start();
                jQuery.ajax({
                    url: "{{url_for('projectProfile.precheck', project_id=project_id)}}",
                    data: this.datas,
                    cache: false,
                    type: "POST",
                    // 告诉jQuery不要去处理发送的数据
                    processData : false,
                    // 告诉jQuery不要去设置Content-Type请求头
                    contentType : false,
                    success: function(response) {
                        spinningModal.show=false;
                        $.AMUI.progress.done();
                        console.log(response);
                        if(response.result == 1){
                            preCheckModal.precheck_ok = true
                            console.log(response.data)
                            preCheckModal.precheckdata = response.data;
                            if(preCheckModal.precheckdata.issue_id_ok && !preCheckModal.precheckdata.issue_id_ok){
                                preCheckModal.precheck_ok = false
                                setTimeout(function(){
                                    $(".issue_id_err").popover({theme: 'danger', content: '请选择正确的故障单号', trigger: 'hover focus'})
                                },500)
                            }else if(preCheckModal.precheckdata.oa_id_ok && !preCheckModal.precheckdata.oa_id_ok){
                                preCheckModal.precheck_ok = false
                                setTimeout(function(){
                                    $(".oa_id_err").popover({theme: 'danger', content: '请选择正确的OA单号', trigger: 'hover focus'})
                                },500)
                            }else if(preCheckModal.precheckdata.sql_status){
                                for(var k in preCheckModal.precheckdata.sql_status){
                                    if(preCheckModal.precheckdata.sql_status[k] == 'not_pass' || preCheckModal.precheckdata.sql_status[k] == 'review'){
                                        preCheckModal.precheck_ok = false
                                        setTimeout(function(){
                                        $(".sql_review_err").popover({theme: 'danger', content: '请重新提交审核并确保审核通过', trigger: 'hover focus'})
                                    },500)
                                    }
                                }
                            }
                            if(preCheckModal.precheckdata.app_info){
                                for(i=0;i<app.app_branch_list.length;i++){
                                    id = String(app.app_branch_list[i].app_id)
                                    preCheckModal.precheckdata.app_info[id]['name'] = app.app_branch_list[i].app_name
                                    preCheckModal.precheckdata.app_info[id]['type'] = app.app_branch_list[i].app_type
                                }
                                for(i=0;i<app.share_branch_list.length;i++){
                                    id = String(app.share_branch_list[i].app_id)
                                    preCheckModal.precheckdata.app_info[id]['name'] = app.share_branch_list[i].app_name
                                    preCheckModal.precheckdata.app_info[id]['type'] = app.share_branch_list[i].app_type
                                }
                            }
                            if(preCheckModal.precheckdata.app_info){
                                for(var key in preCheckModal.precheckdata.app_info){
                                    if(preCheckModal.precheckdata.app_info[key].first_time && preCheckModal.precheckdata.app_info[key].init_version_ok==false){
                                        preCheckModal.precheck_ok = false
                                        setTimeout(function(){
                                            $(".init_version_err").popover({theme: 'danger', content: '新应用第一次发布的POM文件中的版本应该<br>为1.0.0，请撤回项目进行修改，如有问题请联系PE', trigger: 'hover focus'})
                                        },500)
                                    }
                                    //if(!preCheckModal.precheckdata.app_info[key].no_snapshot){
                                    //    preCheckModal.precheck_ok = false
                                    //    setTimeout(function(){
                                    //        $(".no_snapshot_err").popover({theme: 'danger', content: 'POM文件的依赖中，内部二方包(groupId=com.zhongan)的<br>版本中不应包含SNAPSHOT，请撤回项目进行修改', trigger: 'hover focus'})
                                    //    },500)
                                    //}
                                    if(!preCheckModal.precheckdata.app_info[key].pre_has_ecs && preCheckModal.precheckdata.app_info[key].type=='app' && preCheckModal.precheckdata.app_info[key].pre_server_amount!=0){
                                        preCheckModal.precheck_ok = false
                                        setTimeout(function(){
                                            $(".pre_server_err").popover({theme: 'danger', content: '请联系PE为你的应用配置预发服务器', trigger: 'hover focus'})
                                        },500)
                                    }
                                    if(!preCheckModal.precheckdata.app_info[key].prd_has_ecs && preCheckModal.precheckdata.app_info[key].type=='app'){
                                        preCheckModal.precheck_ok = false
                                        setTimeout(function(){
                                            $(".prd_server_err").popover({theme: 'danger', content: '请联系PE为你的应用配置生产服务器', trigger: 'hover focus'})
                                        },500)
                                    }
                                    if(!preCheckModal.precheckdata.app_info[key].pre_merge_result!=undefined && !preCheckModal.precheckdata.app_info[key].pre_merge_result){
                                        preCheckModal.precheck_ok = false
                                        setTimeout(function(){
                                            $(".pre_merge_result_err").popover({theme: 'danger', content: '当前Branch分支与Trunk分支合并测试失败，<br>当前项目代码可能与其它发布中的项目存在<br>冲突，请撤回项目进行修改，如有问题请联系PE', trigger: 'hover focus'})
                                        },500)
                                    }
                                    if(preCheckModal.precheckdata.app_info[key].hasOwnProperty('aut_antx_config') && !preCheckModal.precheckdata.app_info[key].aut_antx_config){
                                        preCheckModal.precheck_ok = false
                                        setTimeout(function(){
                                            $(".aut_antx_config_err").popover({theme: 'danger', content: '自动化测试环境的ANTX配置不完整，<br>请撤回项目到应用与配置页将<br>自动化测试环境的ANTX配置补充完整，如有问题请联系PE', trigger: 'hover focus'})
                                        },500)
                                    }
                                    if((preCheckModal.precheckdata.app_info[key].type=='open' || preCheckModal.precheckdata.app_info[key].type=='module') && preCheckModal.precheckdata.app_info[key].group_id!='com.zhongan' && preCheckModal.precheckdata.app_info[key].group_id!=null){
                                        preCheckModal.precheck_ok = false
                                        setTimeout(function(){
                                            $(".group_id_err").popover({theme: 'danger', content: 'Share包的groupId不是com.zhongan，请修改。', trigger: 'hover focus'})
                                        },500)
                                    }
                                }
                            }
                            preCheckModal.show = true;
                        }else{
                            spinningModal.show=false;
                            errorModal.msg = response.message;
                            errorModal.show = true;
                        }
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        spinningModal.show=false;
                        errorModal.msg='网络连接异常，请稍后重试。';
                        errorModal.show=true;
                    }
                })
            }
        }
    }
});

var preCheckModal = new Vue({
    el: '#preCheckModal',
    data: {
        show: false,
        width: 800,
        precheckdata: {},
        precheck_ok: true,
    },
    methods: {
        close:function () {
            this.show = false;
        },
        commit:function () {
            if(this.precheck_ok){
                this.show = false;
                this.$http.post("{{url_for('projectProfile.apply_publish', project_id=project_id)}}", this.precheckdata).then(
                    function (response) {
                        if(response.data.result == 1){
                            infoModal.msg = '提交发布成功';
                            infoModal.show = true;
                            window.location.reload();
                        }else{
                            errorModal.msg = '提交发布失败';
                            errorModal.show = true;
                        }
                    },function (res) {
                        errorModal.msg='网络连接异常，请稍后重试。';
                        errorModal.show=true;
                    }
                )
            }else{
                infoModal.msg = '预发检查未通过';
                infoModal.show = true;
            }
        }
    }
});

var publishModal = new Vue({
    el: '#publishModal',
    data: {
        dept_code: '',
        issue_id: '',
        scheduled_time: '',
        publish_comment: '',
        type: '',
        oa_id: '',
        oa_img: '',
        width: 800,
        show: false,
        show_oa: false
    },
    methods:{
        close:  function(){
            this.show = false
            this.show_oa = false
            this.reset()
        },
        reset: function(){
            this.issue_id = ''
            this.publish_comment = ''
            this.type = ''
            this.oa_id = ''
        },
        commit: function(){
            var result = this.verify_inputs()
            if(result){
                var form = new FormData()
                form.append('dept_code', this.dept_code)
                form.append('type', this.type)
                form.append('publish_type', $('input[name=publish_type]:checked').val())
                if(this.issue_id){
                    form.append('issue_id', this.issue_id)
                }
                if(basic.regulator_id){
                    form.append('oa_id', 'BUG999OA')
                }else{
                    form.append('oa_id', this.oa_id)
                }
                form.append('oa_img', this.oa_img)
                form.append('scheduled_time', $('#scheduled_time').val())
                form.append('publish_comment', this.publish_comment)
                basicConfirmModal.datas = form
                basicConfirmModal.msg = "确认提交发布并进行发布前预检吗?";
                basicConfirmModal.action = "apply_publish";
                this.close()
                basicConfirmModal.show = true;
            }
        },
        verify_inputs: function(){
            if(this.type=='system_fault' || this.type=='bug_repairs'){
                if(!(this.issue_id  && ($('input[name=publish_type]:checked').length))){
                    errorModal.show = true;
                    errorModal.msg = '*字段以及发布类型为必填项';
                    return false
                }
                if(this.show_oa && !basic.regulator_id){
                    if(!(this.oa_id && this.oa_img)){
                        errorModal.show = true;
                        errorModal.msg = '*为必填项';
                        return false
                    }
                }
                return true
            }else{
                if(!$('input[name=publish_type]:checked').length){
                    errorModal.show = true;
                    errorModal.msg = '发布类型为必填项';
                    return false
                }
                return true
            }
        },
        urgent_publish: function(){
            if(!basic.regulator_id){
                publishModal.show_oa = true
            }
        },
        disable_oa_fields: function(){
            publishModal.show_oa = false
        },
        show_oa_img: function(){
            console.log($('#oa_img').val())
            var fileNames = ''
            if($('#oa_img').val()){
                    fileNames = '<span class="am-badge am-badge-danger"><h3 style="font-size:2em;margin-bottom:0px;">' + $('#oa_img')[0].files[0].name+ '</h3></span> ';
                    this.oa_img = $('#oa_img')[0].files[0]
            }
            $('#show_oa_img').html(fileNames);
        }
    }
});

function update_selected_users(role){
    if(role=='qa'){
        if($('#qa').val()){
            basic.qa = $('#qa').val()
        }else{
            basic.qa = []
        }
    }else if(role=='developer'){
        if($('#developer').val()){
            basic.developer = $('#developer').val()
        }else{
            basic.developer = []
        }
    }else if(role=='code_review'){
        if($('#code_review').val()){
            basic.code_review = $('#code_review').val()
        }else{
            basic.code_review =  []
        }
    }
}

var codeReviewDetailedModal = new Vue({
    el: '#codeReviewDetailedModal',
    data: {
        show: false,
        width: 1000,
        msg: '',
        action: '',
        type: '',
        app_list: [],
        share_list: [],
        antx_list: [],
        diamond_list: [],
        err_msg: '',
        status_ok: true,
        need_review: ''
    },
    methods: {
        close:function () {
            this.show = false;
        },
        commit:function () {
            verifyConfirmModal.commit();
            this.show = false;
        },
        show_code_review:function(){
            codeReviewDetailedModal.err_msg = ''
            codeReviewDetailedModal.status_ok = true
            codeReviewDetailedModal.app_list = app.app_branch_list
            codeReviewDetailedModal.share_list = app.share_branch_list
            codeReviewDetailedModal.antx_list = config.antx_list
            codeReviewDetailedModal.diamond_list = config.diamond_list
            codeReviewDetailedModal.need_review = config.need_review
            this.$http.get("{{url_for('projectProfile.list_project_code_review_status', project_id=project_id)}}").then(
            function(response){
                if(response.data.result==1){
                    response.data.data.forEach(function(e){
                        codeReviewDetailedModal.app_list.forEach(function(f){
                            if(e.app_id.toString()==f.app_id.toString() && e.branch=="branch/"+f.branch && e.commit_revision && e.commit_revision.toString()==f.submit_test.toString()){
                                f.status = e.status;
                            }
                        });
                        codeReviewDetailedModal.share_list.forEach(function(f){
                            if(e.app_id.toString()==f.app_id.toString() && e.branch=="branch/"+f.branch && e.commit_revision && e.commit_revision.toString()==f.submit_test.toString()){
                                f.status = e.status;
                            }
                        });
                    });
                    codeReviewDetailedModal.app_list.forEach(function(e){
                        if(e.submit_test!=e.original && {{config['CODE_REVIEW_LIMIT_DEPT_ID']}}.indexOf(basic.selected_department)>=0){
                            if(e.status=='bad'){
                                codeReviewDetailedModal.err_msg = '所有代码都需要评审通过！'
                                codeReviewDetailedModal.status_ok = false;
                            }else if(e.status=='good'){
                            }else{
                                codeReviewDetailedModal.err_msg = '存在未评审的代码！'
                                codeReviewDetailedModal.status_ok = false;
                            }
                        }
                    });
                    codeReviewDetailedModal.share_list.forEach(function(e){
                        if(e.submit_test!=e.original && {{config['CODE_REVIEW_LIMIT_DEPT_ID']}}.indexOf(basic.selected_department)>=0){
                            if(e.status=='bad'){
                                codeReviewDetailedModal.err_msg = '所有代码都需要评审通过！'
                                codeReviewDetailedModal.status_ok = false;
                            }else if(e.status=='good'){
                            }else{
                                codeReviewDetailedModal.err_msg = '存在未评审的代码！'
                                codeReviewDetailedModal.status_ok = false;
                            }
                        }
                    });
                    codeReviewDetailedModal.antx_list.forEach(function(e){
                        if({{config['CONFIG_CODE_REVIEW_LIMIT_DEPT_ID']}}.indexOf(basic.selected_department)>=0){
                            if(e.review_status=='refuse'){
                                codeReviewDetailedModal.err_msg = '所有代码都需要评审通过！'
                                codeReviewDetailedModal.status_ok = false;
                            }else if(e.review_status=='pass'){
                            }else{
                                codeReviewDetailedModal.err_msg = '存在未评审的代码！'
                                codeReviewDetailedModal.status_ok = false;
                            }
                        }
                    });
                    codeReviewDetailedModal.diamond_list.forEach(function(e){
                        if({{config['CONFIG_CODE_REVIEW_LIMIT_DEPT_ID']}}.indexOf(basic.selected_department)>=0){
                            if(e.review_status=='refuse'){
                                codeReviewDetailedModal.err_msg = '所有代码都需要评审通过！'
                                codeReviewDetailedModal.status_ok = false;
                            }else if(e.review_status=='pass'){
                            }else{
                                codeReviewDetailedModal.err_msg = '存在未评审的代码！'
                                codeReviewDetailedModal.status_ok = false;
                            }
                        }
                    });

                }
                codeReviewDetailedModal.show = true;
            },
            function(res){
                codeReviewDetailedModal.show = true;
            })
        },
        review: function(app_id, branch, original, submit_test, review_token){
            app.review(app_id, branch, original, submit_test, review_token);
            this.show = false;
        },
        review_antx: function(app_id, env){
            showAntxModal.load(app_id, env);
            showAntxModal.need_review = this.need_review
            showAntxModal.code_review_open = true
            showAntxModal.show = true;
        },
        review_diamond: function(data_id, env){
            showDiamondModal.load(env, data_id)
            showDiamondModal.need_review = this.need_review
            showDiamondModal.code_review_open = true
            showDiamondModal.show = true
        }

    }
});