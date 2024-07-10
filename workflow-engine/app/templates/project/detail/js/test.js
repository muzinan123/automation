var test = new Vue({
    el: '#tab4',
    data: {
        request: '',
        api: '',
        smoke: '',
        test_file: '',
        keynote: '',
        submit: false,
    },
    methods: {
        load_test: function(){
            this.$http.get("{{url_for('projectProfile.get_test_details', project_id=project_id)}}").then(
                function(response){
                    if(response.data.result == 1 && response.data.data){
                        this.request = response.data.data.request
                        this.api = response.data.data.api
                        this.smoke = response.data.data.smoke
                        this.keynote = response.data.data.keynote
                        this.test_file = response.data.data.test_file

                        if(basic.code_review_status || '{{session['userId']}}'!= basic.owner_id){
                            test.submit = true
                        }
                        if(test.submit){
                            $('#request').attr('disabled','disabled')
                            $('#api').attr('disabled','disabled')
                            $('#smoke').attr('disabled','disabled')
                            $('#keynote').attr('disabled','disabled')
                            $('#test_result_btn').attr('disabled','disabled')
                        }
                        if(basic.verify_inputs() && test.verify_inputs()){
                            basic.all_ready=true;
                        }
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
        },
        show_test_file: function(){
            var fileNames = ''
            this.test_file = ''
            if($('#test_file').val() && !basic.code_review_status){
                fileNames = '<span class="am-badge am-badge-danger"><h3 style="font-size:2em;margin-bottom:0px;">' + $('#test_file')[0].files[0].name + '</h3></span>'
                $('#show_test_file').html(fileNames);
            }else{
                $('#show_test_file').html('')
            }
        },
        verify_inputs: function(){
            if(!((this.test_file || $('#test_file').val()) && this.keynote)){
                return false;
            }
            return true;
        },
        save: function(){
            if(test.verify_inputs()){
                console.log('save')
                var form = new FormData()
                form.append('request', test.request)
                form.append('api', test.api)
                form.append('smoke', test.smoke)
                form.append('keynote', test.keynote)
                if($('#test_file').val()){
                    form.append('test_file', $('#test_file')[0].files[0])
                }else{
                    form.append('test_file', this.test_file)
                }
                $.AMUI.progress.start();
                jQuery.ajax({
                    url: "{{url_for('projectProfile.update_project_test', project_id=project_id)}}",
                    data: form,
                    cache: false,
                    type: "POST",
                    // 告诉jQuery不要去处理发送的数据
                    processData : false,
                    // 告诉jQuery不要去设置Content-Type请求头
                    contentType : false,
                    timeout : 30000,
                    success: function(response) {
                        $.AMUI.progress.done();
                        console.log(response);
                        if(response.result == 1){
                            infoModal.msg = '操作成功';
                            infoModal.show = true;
                            window.location.reload();
                        }else{
                            errorModal.msg = '保存失败';
                            errorModal.show = true;
                        }
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        errorModal.msg='网络连接异常，请稍后重试。';
                        errorModal.show=true;
                    }
                });
            }else{
                errorModal.msg = '提交测试页中有必填项未填写!';
                errorModal.show = true;
            }
        }
    }
})