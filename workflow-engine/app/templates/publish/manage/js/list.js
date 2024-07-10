    var list = new Vue({
        el: '#list',
        data : {
                publish_list: [],
                active: 'active',
                normal: 'normal',
                },
        methods: {
            go_project: function(project_id){
                window.open("/project/detail/"+project_id, '_blank');
                return false;
            },
            go_publish: function(publish_id){
                window.open("/publish/"+publish_id+"/detail", '_blank');
                return false;
            },
            load_publish_ids: function(){
                this.$http.get("{{url_for('publishProfile.list_publish_ids')}}").then(
                function(response){
                    list.publish_list = []
                    list.load_publish_info(response.data.data);
                },
                function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                })
            },
            load_publish_info: function(ids_list){
                this.$http.post("{{url_for('publishProfile.get_publish_info')}}", ids_list).then(
                function(response){
                    list.publish_list.forEach(function(e, idx){
                        if(ids_list.indexOf(e.publish_id)>=0){
                            list.publish_list.splice(idx, 1)
                        }
                    });

                    if(response.data.result == 1){
                        response.data.data.forEach(function(e){
                            list.publish_list.push(e)
                            list.setTypeClass(e.publish)
                        });
                    }else{
                        errorModal.msg='加载发布信息失败。';
                        errorModal.show=true;
                    }
                },
                function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
            },
            action: function(line, direction, dv){
                if(direction=='app_sort'){
                    this.sort_app(line.project.id, line.publish_id)
                }else if(direction=='change_scheduled_time'){
                    this.change_scheduled_time(line.publish_id, line.publish.scheduled_time)
                }else if(direction=='pre_not_pass' || direction=='local_not_pass'){
                    rollbackModal.action=direction
                    rollbackModal.show = true
                    rollbackModal.target = line.publish_id
                    rollbackModal.project_id = line.project.id
                    rollbackModal.list_all_participant()
                }else if(direction=='prd_build'){
                    app_id_list = []
                    line.publish.app_order.forEach(function(e){
                        if(!line.publish.app_info[e].skip){
                            app_id_list.push(e)
                        }
                    })
                    line.publish.share_order.forEach(function(e){
                        if(!line.publish.app_info[e].skip){
                            app_id_list.push(e)
                        }
                    })
                    if(line.publish.dzbd && !line.publish.dzbd.skip){
                        app_id_list.push(line.publish.dzbd.app_id)
                    }
                    prdBuildModal.load_hot_app(app_id_list, line.publish_id)
                    prdBuildModal.action=direction
                    prdBuildModal.show=true
                    prdBuildModal.target=line.publish_id
                }else if(direction == 'pre_change_label'){
                    //预发环境
                    this.change_success_label(line.project.id, line.publish_id, "pre")
                }else if(direction == 'prd_change_label'){
                    //生产环境
                    this.change_success_label(line.project.id, line.publish_id ,"prd")
                }else{
                    actionConfirmModal.msg='确定要执行 <b>'+dv.name+'</b> 操作吗?'
                    actionConfirmModal.action=direction
                    actionConfirmModal.show=true
                    actionConfirmModal.target=line.publish_id
                }
            },
            change_success_label: function(project_id, publish_id, env){
                setSuccessModal.show = true
                setSuccessModal.publish_id = publish_id.toString()
                setSuccessModal.project_id = project_id.toString()
                setSuccessModal.initialization(publish_id, project_id, env);

            },
            sort_app: function(project_id, publish_id){
                sortAppModal.show = true
                sortAppModal.edit_success = 0;
                sortAppModal.publish_id = publish_id.toString()
                sortAppModal.project_id = project_id.toString()
                sortAppModal.load()
            },
            change_scheduled_time: function(publish_id, scheduled_time){
                changeScheduledTimeModal.show = true
                changeScheduledTimeModal.publish_id = publish_id
                changeScheduledTimeModal.scheduled_time = scheduled_time
                now = new Date()
                now_date = formatDate(now)
                setTimeout(function(){
                    $('#scheduled_time').datetimepicker({format: 'YYYY-MM-DD HH:mm'});
                    $('#scheduled_time').data('DateTimePicker').minDate(now_date)
                }, 500)
            },
            setTypeClass: function(publish){
                if(publish.current_flow_info.env!='local'){
                    var env = publish.current_flow_info.env
                    var sql_before_exe = env+"_sql_before_executed"
                    var sql_after_exe = env+"_sql_after_executed"
                    publish['sql_active'] = false

                    if(publish.sql_execute_config && publish.sql_status[env] != 'init'){
                        if(!publish[sql_before_exe] && !publish[sql_after_exe]){
                            publish['sql_active'] = true
                        }
                    }
                }

                publish['pe_participanted_in'] = false
                publish['dba_participanted_in'] = false
                if(publish.participants.length>0){
                    publish.participants.forEach(function(one){
                        if(one.privilege_name=='pe'){
                            publish['pe_participanted_in'] = true;
                        }
                        if(one.privilege_name=='dba'){
                            publish['dba_participanted_in'] = true;
                        }
                    });
                }
            }
        }
    });

    var actionConfirmModal = new Vue({
        el: '#actionConfirmModal',
        data : {
            show: false,
            width: 500,
            msg: '',
            action: '',
            target: ''
        },
        methods: {
            close: function() {
                this.show=false;
            },
            commit: function() {
                this.show=false;
                this.$http.post("{{url_for('flowProfile.publish_flow')}}", {'flow_id':this.target,'direction':this.action}, {emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        list.load_publish_info([this.target]);
                    }else{
                        errorModal.msg='流程操作失败。';
                        errorModal.show=true;
                    }
                },
                function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                })
            }
        }
    });

    var rollbackModal = new Vue({
        el: '#rollbackModal',
        data : {
            show: false,
            width: 500,
            target: '',
            project_id: '',
            reason: '',
            comment: '',
            participant: [],
            bad_man: '',
        },
        methods: {
            close: function() {
                this.show=false;
            },
            list_all_participant: function(){
                this.$http.get("{{url_for('projectProfile.list_all_participant')}}", {'params':{'project_id':this.project_id}, emulateJSON: true}).then(
                function(response){
                    rollbackModal.bad_man = '';
                    rollbackModal.participant = response.data.data;
                },
                function(res){
                    errorModal.msg = '网络连接异常，请稍后重试。';
                    errorModal.show = true;
                })
            },
            commit: function() {
                if(this.reason){
                    if(this.action=='pre_not_pass'){
                        flow_data_change = '{"data.pre_not_pass_reason": "' + this.reason + '", "data.pre_not_pass_comment": "' + this.comment + '", "data.bad_man": "'+this.bad_man+'"}'
                    }else if(this.action=='local_not_pass'){
                        flow_data_change = '{"data.owner_rollback_reason": "' + this.reason + '", "data.owner_rollback_comment": "' + this.comment + '", "data.bad_man": "'+this.bad_man+'"}'
                    }
                    this.show=false;
                    this.$http.post("{{url_for('flowProfile.publish_flow')}}", {'flow_id':this.target,'direction':this.action, 'flow_data_change':flow_data_change}, {emulateJSON: true}).then(
                    function(response){
                        if(response.data.result == 1){
                            list.load_publish_info([this.target]);
                        }else{
                            errorModal.msg='流程操作失败。';
                            errorModal.show=true;
                        }
                    },
                    function(res){
                        errorModal.msg='网络连接异常，请稍后重试。';
                        errorModal.show=true;
                    })
                }
            }
        }
    });

    var prdBuildModal = new Vue({
        el: '#prdBuildModal',
        data : {
            show: false,
            width: 600,
            msg: '',
            action: '',
            target: '',
            flag: '',
            prd_app_list_1: [],
            prd_app_list_2: []
        },
        methods: {
            close: function() {
                this.show=false;
            },
            commit: function() {
                if(this.flag=='has_down' || this.flag=='has_up_and_down'){
                    //先skip
                    this.show=false;
                    this.$http.post("{{url_for('publishProfile.publish_skip_prd_app')}}", this.prd_app_list_1).then(
                    function(response){
                        if(response.data.result == 1){
                            this.$http.post("{{url_for('flowProfile.publish_flow')}}", {'flow_id':prdBuildModal.target,'direction':prdBuildModal.action}, {emulateJSON: true}).then(
                            function(response){
                                if(response.data.result == 1){
                                    window.location.reload();
                                }else{
                                    errorModal.msg='流程操作失败。';
                                    errorModal.show=true;
                                }
                            },
                            function(res){
                                errorModal.msg='网络连接异常，请稍后重试。';
                                errorModal.show=true;
                            })
                        }else{
                            errorModal.msg='流程操作失败。';
                            errorModal.show=true;
                        }
                    },
                    function(res){
                        errorModal.msg='网络连接异常，请稍后重试。';
                        errorModal.show=true;
                    })
                }else{
                    this.show=false;
                    this.$http.post("{{url_for('flowProfile.publish_flow')}}", {'flow_id':prdBuildModal.target,'direction':prdBuildModal.action}, {emulateJSON: true}).then(
                    function(response){
                        if(response.data.result == 1){
                            list.load_publish_info([prdBuildModal.target]);
                        }else{
                            errorModal.msg='流程操作失败。';
                            errorModal.show=true;
                        }
                    },
                    function(res){
                        errorModal.msg='网络连接异常，请稍后重试。';
                        errorModal.show=true;
                    })
                }
            },
            load_hot_app: function(app_id_list, publish_id) {
                this.$http.post("/publish/"+publish_id+"/check_prd_hot_app", app_id_list).then(
                function(response){
                    this.flag=response.data.flag;
                    if(response.data.flag == 'has_down'){
                        //有需要合并发布的应用
                        this.msg='该发布单中以下应用的版本比其它发布单中相同应用的版本更高，其它发布单中的相同应用将无需(buhui)发布，是否继续?'
                        this.prd_app_list_1 = response.data.down_data;
                        this.prd_app_list_2 = [];
                    }else if(response.data.flag == 'has_up'){
                        //有相同应用正在打包
                        this.msg='该发布单中以下应用的版本比其它发布单中相同应用的版本更低，推荐发布其它的发布单，避免重复发布，是否仍要继续?'
                        this.prd_app_list_1 = response.data.up_data;
                        this.prd_app_list_2 = [];
                    }else if(response.data.flag == 'has_up_and_down'){
                        //有相同应用正在打包
                        this.msg='该发布单中以下应用的版本比其它发布单中相同应用的版本更高或更低, 推荐发布其它的发布单，避免重复发布，是否仍要继续?'
                        this.prd_app_list_1 = response.data.down_data;
                        this.prd_app_list_2 = response.data.up_data;
                    }else if(response.data.flag == 'has_not_ready'){
                        //有相同应用正在打包
                        this.msg='该发布单中以下应用在其它发布单中还有未执行的SQL，无法操作!'
                        this.prd_app_list_1 = response.data.not_ready_data;
                        this.prd_app_list_2 = [];
                    }else if(response.data.flag == 'has_running'){
                        //有相同应用正在打包
                        this.msg='该发布单中以下应用正由其它发布单打包发布中，无法操作!'
                        this.prd_app_list_1 = response.data.running_data;
                        this.prd_app_list_2 = [];
                    }else if(response.data.flag == 'ok'){
                        //没有需要合并发布的应用
                        this.msg='确定要执行 <b>打包</b> 操作吗?'
                        this.prd_app_list_1 = [];
                        this.prd_app_list_2 = [];
                    }
                },
                function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                })
            }
        }
    });

    var changeScheduledTimeModal = new Vue({
        el: '#changeScheduledTimeModal',
        data: {
            show: false,
            width: 400,
            publish_id: '',
            scheduled_time: ''
        },
        methods: {
            close: function() {
                this.show=false;
            },
            commit: function() {
                this.scheduled_time = $("#scheduled_time").val()
                this.$http.post("/publish/"+this.publish_id+"/change_scheduled_time", {'scheduled_time': this.scheduled_time}, {emulateJSON: true}).then(
                function(response){
                    this.show=false;
                    if(response.data.result==1){
                        list.load_publish_info([this.publish_id]);
                    }else{
                        errorModal.msg='修改发布单定时发布时间失败，请确认所修改的时间比当前时间晚。如果生产区已经有相同应用定时发布，只能指定<b>更晚</b>的时间进行定时发布。';
                        errorModal.show=true;
                    }
                },
                function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                })
            }
        }
    })

    var setSuccessModal = new Vue({
        el: '#setSuccessModal',
        data: {
            show: false,
            width: 1300,
            publish_id: '',
            project_id: '',
            has_dzbd: false,
            dzbd_published:[],
            app_infos:{},
            app_list:[],
            env:'',
            published:'',
        },
        methods: {
            close: function() {
                this.show=false;
            },
            initialization: function(publish_id,project_id,env){
                if(env == "prd"){
                    this.env = "prd";
                }else if(env == "pre"){
                    this.env = "pre";
                }
                this.dzbd_published = []
                this.app_infos = {}
                this.has_dzbd = false;
                list.publish_list.forEach(function(e){
                    if(e.publish.project_id == project_id){
                        if(e.publish.hasOwnProperty("dzbd")){
                            setSuccessModal.has_dzbd = true;
                            if(env == "prd" && e.publish.dzbd.hasOwnProperty("published_prd_servers")){
                                setSuccessModal.dzbd_published=e.publish.dzbd.published_prd_servers;
                            }else if(env == "pre" && e.publish.dzbd.hasOwnProperty("published_pre_servers")){
                                setSuccessModal.dzbd_published=e.publish.dzbd.published_pre_servers;
                            }
                        }
                        if(e.publish.hasOwnProperty("app_info")){
                            if (Object.keys(e.publish.app_info).length > 0) {
                                setSuccessModal.app_infos = e.publish.app_info
                            }
                        }
                    }
                })
                this.app_info_list(project_id);
                setTimeout("setSuccessModal.tags_input()", 100);
            },
            app_info_list:function(project_id){
                this.app_list = []
                for(var key in this.app_infos){
                    one = this.app_infos[key];
                    dict = {'app_id': key ,"app_name":one.name,"app_type":one.type, "published":[],"built":false}
                    if(one.hasOwnProperty("published_pre_servers") && setSuccessModal.env == "pre"){
                        dict["published"]=one.published_pre_servers
                    }else if(one.hasOwnProperty("published_prd_servers") && setSuccessModal.env == "prd"){
                        dict["published"]=one.published_prd_servers
                    }
                    if(one.hasOwnProperty("pre_built") && setSuccessModal.env == "pre"){
                        dict["built"]=one.pre_built
                    }else if(one.hasOwnProperty("prd_built") && setSuccessModal.env == "prd"){
                        dict["built"]=one.prd_built
                    }
                    setSuccessModal.app_list.push(dict)
                }
            },
            tags_input:function(){
                $('#dzbd-published').tagsinput()
                $('.app-published').tagsinput()
            },
            commit: function() {
                var flow_data_data = {}
                flow_data_data['env'] = this.env
                flow_data_data['flow_id'] = this.publish_id

                if(this.has_dzbd){
                    //电子表单
                    var dzbd = $('#dzbd-published').val();
                    flow_data_data['dzbd'] = dzbd
                }

                if(this.app_list.length>0){
                    //应用
                    var published_servers = []
                    var app_list = this.app_list
                    $(".app-published").each(function () {
                        published_servers.push($(this).val());
                    });
                    for(var i=0;i<published_servers.length;i++){
                        if(app_list[i]["app_type"]=='app'){
                            if(published_servers[i]==null){
                                app_list[i]["published"] = []
                            }else{
                                app_list[i]["published"] = published_servers[i]
                            }
                        }
                    }
                    flow_data_data['app_list'] = app_list
                }

                if(this.has_dzbd || this.app_list.length>0){
                    this.$http.post("{{url_for('publishProfile.update_flow_data')}}", flow_data_data).then(
                    function(response){
                       if(response.data.result == 1){
                            infoModal.msg = '保存成功'
                            window.location.reload();
                       }else{
                            errorModal.msg='保存失败';
                            errorModal.show=true;
                       }
                    },function(res){
                        console.log(res);
                        errorModal.msg='网络连接异常，请稍后重试。';
                        errorModal.show=true;
                    })
                }
            }
        }
    })