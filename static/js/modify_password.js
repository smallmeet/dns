/**!
 * 修改密码
 */
(function($) {
    'use strict';

    var moduleModifyPassword = {
        'init': function() {
            this.bindViews();
            this.bindEvents();
        },
        'bindViews': function() {
            this.$dialogContainer = $('#modal-modify-password');
            this.$inputOldPwd = $('#input-old-password');
            this.$inputNewPwd = $('#input-new-password');
            this.$inputNewPwdRepeat = $('#input-new-password-repeat');
            this.$btnClose = this.$dialogContainer.find('button.close');
            this.$btnCancel = this.$dialogContainer.find('button.cancel');
            this.$btnSubmit = this.$dialogContainer.find('button.submit');
        },
        'bindEvents': function() {
            this.$btnClose.on('click', this.reset.bind(this));
            this.$btnCancel.on('click', this.reset.bind(this));
            this.$btnSubmit.on('click', this.submit.bind(this));
        },
        'reset': function() {
            this.$inputOldPwd.val('');
            this.$inputNewPwd.val('');
            this.$inputNewPwdRepeat.val('');
        },
        'submit': function() {
            var oldPwd = this.$inputOldPwd.val(),
                newPwd = this.$inputNewPwd.val(),
                newPwdRepeat = this.$inputNewPwdRepeat.val();
            if (newPwd !== newPwdRepeat) {
                myalert('两次输入的密码不一致');
            } else {
                $.post('/modify_password', {
                    'old_pwd': oldPwd,
                    'new_pwd': newPwd
                }, this.callback.bind(this), 'json');
            }
        },
        'callback': function(data) {
            if (data.success) {
                this.$dialogContainer.modal('hide');
                myalert('修改成功', 'tipright');
            } else {
                myalert('原密码错误。')
            }
        },
    };
    moduleModifyPassword.init();
}) (jQuery);