
var showAntxModal = new Vue({
   el: '#showAntxModal',
   data: {
        show: false,
	    width: 1300,
	    app_id: '',
        app_name: '',
        env: '',
        diff_list: [],
        need_review: '',
        review_status: '',
        code_review_open: ''
   },
   methods: {
       close: function(){
           this.show = false
           this.code_review_open = ''
       },
       load: function(app_id, env){
           this.$http.get("{{url_for('antxProfile.project_antx')}}", {params: {'action': 'show', 'project_id': '{{project_id}}', 'env': env, 'app_id': app_id}, emulateJSON: true}).then(
           function(response){
               if(response.data.result == 1){
                   showAntxModal.env = response.data.data.env;
                   showAntxModal.app_name = response.data.data.app_name;
                   showAntxModal.app_id = app_id
                   showAntxModal.review_status = response.data.data.review_status
                   showAntxModal.diff_list = [];
                   response.data.data.diff.forEach(function(e){
                       showAntxModal.diff_list.push(e)
                   });
               }
           },function(res){
               errorModal.msg='网络连接异常，请稍后重试。';
               errorModal.show=true;
           });
       },
       project_antx_review: function(review_status){
           this.$http.post("{{url_for('antxProfile.project_antx_review')}}", {'app_name': this.app_name, 'project_id': '{{project_id}}', 'env': this.env, 'app_id': this.app_id, 'review_status': review_status}).then(
           function(response){
                if(response.data.result == 1){
                    this.show = false
                    if(review_status=='refuse'){
                         verifyConfirmModal.type = "project";
                         verifyConfirmModal.action = "rollback";
                         verifyConfirmModal.commit()
                    }else{
                         infoModal.msg = '审批状态修改成功';
                         infoModal.show = true
                         config.load()
                    }
                }
           },function(res){
               errorModal.msg='网络连接异常，请稍后重试。';
               errorModal.show=true;
           });
       }
   }
});

var newAntxModal = new Vue({
    el: '#newAntxModal',
    data: {
        show: false,
	    width: 800,
        app_list: []
    },
    methods: {
        commit: function(){
            app_env_list = [];
            for(i=0;i<newAntxModal.app_list.length;i++){
                one = {'app_id': 0, 'app_name':'', 'env_list': []}
                var app = newAntxModal.app_list[i].app_name
                var pre_check = $('#'+app+'_pre_env').prop('checked')
                var pre_check_disabled = $('#'+app+'_pre_env').prop('disabled')
                var prd_check = $('#'+app+'_prd_env').prop('checked')
                var prd_check_disabled = $('#'+app+'_prd_env').prop('disabled')
                var aut_check = $('#'+app+'_aut_env').prop('checked')
                var aut_check_disabled = $('#'+app+'_aut_env').prop('disabled')

                if(pre_check && !pre_check_disabled){
                    one.env_list.push('pre')
                }
                if(prd_check && !prd_check_disabled){
                    one.env_list.push('prd')
                }
                if(aut_check && !aut_check_disabled){
                    one.env_list.push('aut')
                }
                if(one.env_list.length){
                    one.app_id = this.app_list[i].app_id
                    one.app_name = this.app_list[i].app_name
                    app_env_list.push(one)
                }
            }
            if(app_env_list.length){
                this.$http.put("{{url_for('antxProfile.project_antx')}}", {'project_id': '{{project_id}}', 'app_env_list': app_env_list}).then(
                function(response){
                    if(response.data.result == 1){
                        this.show = false;
                        this.reset();
                        config.load()
                 }else{
                        this.reset();
                        errorModal.msg=response.data.message;
                        errorModal.show=true;
                 }},function(res){
                        this.reset();
                        errorModal.msg='网络连接异常，请稍后重试。';
                        errorModal.show=true;
                 });
            }
        },
        close: function(){
            this.show = false;
            this.reset()
        },
        reset: function() {
            this.env = '';
            this.checked = false;
            this.app_idx = '';
            this.app_name = '';
            this.app_id = '';
            this.width = 800;
        }
    },

});

var editAntxModal = new Vue({
    el: '#editAntxModal',
    data: {
        show: false,
	    width: 1300,
        app_name: '',
        app_id: 0,
        env: '',
        content: '',
        content_list: [],
        kv_edit: false,
    },
    methods: {
        close: function(){
            this.show = false
        },
        load: function(app_id, env){
            this.app_id = app_id
            this.$http.get("{{url_for('antxProfile.project_antx')}}", {params: {'action': 'edit', 'project_id': '{{project_id}}', 'env': env, 'app_id': app_id}, emulateJSON: true}).then(
            function(response){
                if(response.data.result == 1){
                    editAntxModal.env = response.data.data.env;
                    editAntxModal.app_name = response.data.data.app_name;
                    editAntxModal.content_list = [];
                    editAntxModal.content = ''
                    content = []
                    response.data.data.content.forEach(function(e){
                        content.push( e.k + " = " + e.v);
                    })
                    editAntxModal.content = content.join("\r\n");
                    setTimeout('$("#editAntxModalcontent").css("height",($("#editAntxModalcontent")[0].scrollHeight+2)+"px")', 10);
                }
            },function(res){
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
        },
        commit: function(){
            content_list = []
            editAntxModal.content_list.forEach(function(l, idx){
                if(!l.k && !l.v){
                    //white line
                }else if(!l.k || !l.v){
                    errorModal.msg='格式检查发现错误，请修改正确后再保存。';
                    errorModal.show=true;
                    return;
                }else if(hasChinese(l.k) || hasChinese(l.v)){
                    errorModal.msg='ANTX目前不支持中文内容，请修改正确后再保存。';
                    errorModal.show=true;
                    return;
                }else{
                    content_list.push(l)
                }
            });
            if(content_list.length){
                this.$http.post("{{url_for('antxProfile.project_antx')}}", {'project_id': '{{project_id}}', 'env': this.env, 'app_id': this.app_id, 'content':content_list}).then(
                function(response){
                    if(response.data.result == 1){
                        infoModal.msg='保存成功。';
                        infoModal.show=true;
                        config.load()
                        this.show = false
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
            }else{
                this.show = false
            }
        }
    },
    watch: {
        content: function(val){
            editAntxModal.content_list = [];
            val.split("\n").forEach(function(l){
                e = l.split("=")
                if(e.length>1){
                    k = e.splice(0,1)[0].trim()
                    v = e.join("=").trim()
                    editAntxModal.content_list.push({'k':k,'v':v})
                }else if(e.length==1){
                    editAntxModal.content_list.push({'k':e[0].trim(),'v':''})
                }else{
                    editAntxModal.content_list.push({'k':'','v':''})
                }
            });
            $("#editAntxModalcontent").css('height',($("#editAntxModalcontent")[0].scrollHeight+2)+"px")
        },
        kv_edit: function(val){
            if(this.kv_edit){
                this.width = 2000;
            }else{
                this.width = 1200;
            }
        }
    }
});
