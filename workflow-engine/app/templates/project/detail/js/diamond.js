
var showDiamondModal = new Vue({
    el: '#showDiamondModal',
    data: {
        show: false,
	    width: 1300,
        data_id: '',
        env: '',
        version: '',
        m_type: '',
        need_review: '',
        review_status: '',
        code_review_open: ''
    },
    methods: {
        close: function(){
            this.show = false
            },
        load: function(env, data_id){
            this.$http.get("{{url_for('diamondProfile.project_diamond')}}", {params: {'action':'show', 'project_id': '{{project_id}}', 'env': env, 'data_id': data_id}, emulateJSON: true}).then(
            function(response){
                //console.log();
                if(response.data.result == 1){
                    showDiamondModal.env = response.data.data.env;
                    showDiamondModal.data_id = response.data.data.data_id;
                    showDiamondModal.m_type = response.data.data.m_type;
                    showDiamondModal.review_status = response.data.data.review_status
                    var diffJson = Diff2Html.getJsonFromDiff(response.data.data.diff);
                    $("#side-by-side").html(Diff2Html.getPrettyHtml(diffJson, { inputFormat: 'json', outputFormat: 'side-by-side',synchronisedScroll: true}));
                    $(".d2h-files-diff").width($("#mainForm").width());
                }
            },function(res){
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
        },
        project_diamond_review: function(review_status){
           this.$http.post("{{url_for('diamondProfile.project_diamond_review')}}", {'data_id': this.data_id, 'project_id': '{{project_id}}', 'env': this.env,  'review_status': review_status}).then(
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

var newDiamondModal = new Vue({
    el: '#newDiamondModal',
    data: {
        show: false,
	    width: 800,
        data_id: '',
        env: 'test',
        m_type: 'after',
        content: '',
        base_content: '',
        base_version: '',
        checked: false,
        mode: '',
        saved: false,
    },
    methods: {
        search: function(){
            if(newDiamondModal.data_id.trim().length>0){
                newDiamondModal.data_id=newDiamondModal.data_id.trim();
                newDiamondModal.mode='edit';
                newDiamondModal.load_base();
            }
        },
        add: function(){
            if(newDiamondModal.data_id.trim().length>0){
                newDiamondModal.data_id=newDiamondModal.data_id.trim();
                newDiamondModal.mode='new';
                newDiamondModal.load_base();
            }
        },
        load_base: function(){
            this.$http.get("{{url_for('diamondProfile.base_diamond')}}", {params: {'env': newDiamondModal.env, 'data_id': newDiamondModal.data_id}, emulateJSON: true}).then(
            function(response){
                newDiamondModal.width = 1300;
                newDiamondModal.base_content = '';
                newDiamondModal.base_version = 1
                if(response.data.result == 1){
                    newDiamondModal.base_content = response.data.data.base_content;
                    newDiamondModal.base_version = response.data.data.base_version;
                }
            },function(res){
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
        },
        commit: function(){
            if(newDiamondModal.mode){
                this.$http.put("{{url_for('diamondProfile.project_diamond')}}", {'project_id': '{{project_id}}', 'env': newDiamondModal.env, 'data_id': newDiamondModal.data_id, 'm_type':newDiamondModal.m_type, 'content':newDiamondModal.content, 'base_content':newDiamondModal.base_content, 'base_version':newDiamondModal.base_version}).then(
                function(response){
                    if(response.data.result == 1){
                        newDiamondModal.saved = true;
                        infoModal.msg=response.data.message;
                        infoModal.show=true;
                        config.load()
                        this.show = false
                        this.reset()
                    }else{
                        errorModal.msg=response.data.message ;
                        errorModal.show=true;
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
            }
        },
        reset: function(){
            this.data_id =  ''
            this.env = 'test'
            this.m_type = 'after'
            this.content =  ''
            this.base_content = ''
            this.base_version = ''
            this.checked = false
            this.mode = ''
            this.saved = true
            this.width = 800;
        },
        close: function(){
            this.show = false
            this.reset()
        }
    },
    watch: {
        base_content: function(val){
            if(newDiamondModal.mode){
                if(newDiamondModal.mode=='edit' && val && val.length>0){
                    newDiamondModal.checked=true;
                    newDiamondModal.content = val;
                    setTimeout('$("#newDiamondModalContent").css("height",($("#newDiamondModalContent")[0].scrollHeight+2)+"px")', 10);
                }else if(newDiamondModal.mode=='new' && (!val || val.length==0)){
                    newDiamondModal.checked=true;
                    newDiamondModal.content = '';
                    setTimeout('$("#newDiamondModalContent").css("height",($("#newDiamondModalContent")[0].scrollHeight+2)+"px")', 10);
                }else if(newDiamondModal.mode=='new'){
                    infoModal.msg='dataId已存在，无法新增。';
                    infoModal.show=true;
                    newDiamondModal.mode = '';
                    newDiamondModal.base_content = '';
                }else if(newDiamondModal.mode=='edit'){
                    infoModal.msg='dataId不存在，无法编辑。';
                    infoModal.show=true;
                    newDiamondModal.mode = '';
                    newDiamondModal.base_content = '';
                }
            }
        }
    }
});

var editDiamondModal = new Vue({
    el: '#editDiamondModal',
    data: {
        show: false,
	    width: 1300,
        data_id: '',
        env: '',
        version: '',
        m_type: 'after',
        content: '',
    },
    methods: {
        close: function(){
            this.show = false
         },
        load: function(env, data_id){
            this.$http.get("{{url_for('diamondProfile.project_diamond')}}", {params: {'action':'edit', 'project_id': '{{project_id}}', 'env': env, 'data_id': data_id}, emulateJSON: true}).then(
            function(response){
                //console.log();
                if(response.data.result == 1){
                    editDiamondModal.env = response.data.data.env;
                    editDiamondModal.data_id = response.data.data.data_id;
                    editDiamondModal.m_type = response.data.data.m_type;
                    editDiamondModal.content = response.data.data.content;
                    setTimeout('$("#editDiamondModalContent").css("height",($("#editDiamondModalContent")[0].scrollHeight+2)+"px")', 10);
                }
            },function(res){
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
        },
        commit: function(){
            this.$http.post("{{url_for('diamondProfile.project_diamond')}}", {'project_id': '{{project_id}}', 'env': this.env, 'data_id': this.data_id, 'm_type':this.m_type, 'content':this.content}).then(
            function(response){
                infoModal.msg=response.data.message;
                infoModal.show=true;
                this.show = false
            },function(res){
                errorModal.msg='网络连接异常，请稍后重试。';
                errorModal.show=true;
            });
        }
    },
    watch: {
        content: function(val){
            $("#editDiamondModalContent").css('height',($("#editDiamondModalContent")[0].scrollHeight+2)+"px")
        }
    }
});
