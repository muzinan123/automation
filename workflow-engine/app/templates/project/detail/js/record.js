var record = new Vue({
    el: '#tab3',
    data: {
        record_list: []
    },
    methods: {
        load_record:function () {
            this.$http.get("{{url_for('projectProfile.record_list', project_id=project_id)}}",{emulateJSON: true}).then(
            function (response) {
                if(response.data.success == 1){
                    this.record_list = response.data.data;
                    if(this.record_list.length>0){
                        basic.record = true
                    }
                }
            })
        }
    }
});

var reviewDetailModal = new Vue({
    el: "#reviewDetailModal",
    data: {
        show: false,
        width: 800,
        sql_svn_path: '',
        revision: 0,
        content: ''
    },
    methods:{
        close: function(){
            this.sql_svn_path = ''
            this.revision = 0
            this.show = false
        }
    }
})
var changeBadManModal = new Vue({
    el: '#changeBadManModal',
    data : {
        show: false,
        width: 500,
        target: '',
        project_id: '{{project_id}}',
        participant: [],
        bad_man: '',
        record_id: '',
        publish_id: '',
        operator_id: '',
        reason: '',
        rollback_type: ''
    },
    methods: {
        close: function() {
            this.show=false;
        },
        list_all_participant: function(){
            this.$http.get("{{url_for('projectProfile.list_all_participant')}}", {'params':{'project_id':this.project_id}, emulateJSON: true}).then(
            function(response){
                changeBadManModal.bad_man = '';
                changeBadManModal.participant = response.data.data;
            },
            function(res){
                errorModal.msg = '网络连接异常，请稍后重试。';
                errorModal.show = true;
            })
        },
        commit: function() {
            if(this.bad_man){
                this.show=false;
                this.$http.post("{{url_for('projectProfile.change_bad_man')}}", {'record_id': this.record_id, 'publish_id': this.publish_id, 'operator_id': this.operator_id, 'reason': this.reason, 'bad_man': this.bad_man, 'rollback_type': this.rollback_type}, {emulateJSON: true}).then(
                function(response){
                    record.load_record();
                },
                function(res){
                    errorModal.msg = '网络连接异常，请稍后重试。';
                    errorModal.show = true;
                })
            }
        }
    }
});

function change_bad_man(e, publish_id, operator_id, reason, rollback_type){
    if("{{session['userId']}}"==operator_id){
        record_id = $(e).parent().parent().attr('tag')
        changeBadManModal.record_id = record_id;
        changeBadManModal.publish_id = publish_id;
        changeBadManModal.operator_id = operator_id;
        changeBadManModal.reason = reason;
        changeBadManModal.rollback_type = rollback_type;
        changeBadManModal.list_all_participant();
        changeBadManModal.show = true;
    }
}

function show_review_detail(sql_svn_path, revision){
    reviewDetailModal.sql_svn_path = sql_svn_path
    reviewDetailModal.revision = revision
    $.AMUI.progress.start();
    jQuery.ajax({
        url: "{{url_for('projectProfile.get_sql_review_detail')}}",
        dataType: "json",
        data: {'sql_svn_path': sql_svn_path, 'revision': revision},
        type: "POST",
        timeout : timeout,
        success: function(response) {
            $.AMUI.progress.done();
            if(response.result == 1){
                reviewDetailModal.content = response.data
                reviewDetailModal.show = true
            }else{
                errorModal.msg = response.data.info;
                errorModal.show = true;
            }
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            $.AMUI.progress.done();
                //call failed
            console.log("error");
            errorModal.msg='网络连接异常，请稍后重试。';
            errorModal.show=true;
        }
    });
 }