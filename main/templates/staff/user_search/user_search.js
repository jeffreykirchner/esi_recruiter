axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = new Vue({
    delimiters: ['[[', ']]'],
    el: '#root',        
    data:{
        baseURL:'{{request.get_full_path}}',                                                                                                                 
        users:[],      
        searchInfo:"", 
        warningText:"",
        searchButtonText:'Search <i class="fas fa-search"></i>',
        blackBallButtonText : 'Blackballs',
        noShowButtonText : 'No-Show Blocks',
        activeOnly:true,
        searchCount:0,                        //user found during search
        sendMessageButtonText:"Send Message <i class='fas fa-envelope fa-xs'></i>",         //send message button text
        sendMessageSubject:"",               //subject of send message     
        sendMessageText:"[first name],\n\n[contact email]",          //text of send message     
        emailMessageList:"",                 //emails for send message
    },

    methods:{
        //get list of users based on search
        getUsers: function(){
            if(app.$data.searchButtonText == '<i class="fas fa-spinner fa-spin"></i>') return;

            app.$data.searchButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {                            
                action:"getUsers",
                searchInfo:app.$data.searchInfo,
                activeOnly:app.$data.activeOnly,                                
            })
            .then(function (response) {                         
                app.functionTakeUserList(response);
                app.$data.searchButtonText = 'Search <i class="fas fa-search"></i>';
            })
            .catch(function (error) {
                console.log(error);                               
            }); 
        }, 

        //get all active black balls
        getBlackballs: function(){
            if(app.$data.blackBallButtonText == '<i class="fas fa-spinner fa-spin"></i>') return;

            app.$data.blackBallButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {                            
                action:"getBlackBalls",
                activeOnly:app.$data.activeOnly,                                
            })
            .then(function (response) {                         
                app.functionTakeUserList(response);
                app.$data.blackBallButtonText = 'Blackballs';
            })
            .catch(function (error) {
                console.log(error);                               
            }); 
        },

        //get all no show violators    
        getNoShowBlocks: function(){
            if(app.$data.noShowButtonText == '<i class="fas fa-spinner fa-spin"></i>') return;

            app.$data.users = []
            app.$data.warningText = "";
            app.$data.noShowButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {                            
                action:"getNoShows",
                activeOnly:app.$data.activeOnly,                                
            })
            .then(function (response) {                         
                app.functionTakeUserList(response);
                app.$data.noShowButtonText = 'No-Show Blocks';
            })
            .catch(function (error) {
                console.log(error);                               
            }); 
        },    

        //process incoming user list
        functionTakeUserList:function(response){
            if(response.data.errorMessage != "")
            {
                app.$data.warningText = "Error: " + response.data.errorMessage;
                app.$data.users = [];
            }
            else
            {
                app.$data.users=JSON.parse(response.data.users);

                if(app.$data.users.length == 0)
                {
                    app.$data.warningText="No users found."
                }
                else
                {
                    app.$data.warningText="";
                }

                app.$data.searchCount = app.$data.users.length;
            }                           
        },                                   

        // fire when invite subjects subjects model is shown
        showSendMessage:function(id){    
            $('#sendMessageModalCenter').modal('show');                        
        },

        //fire when hide invite subjects  model, cancel action if nessicary
        hideSendMessage:function(){ 
            if(app.$data.sendMessageButtonText == "Send Message <i class='fas fa-envelope fa-xs'></i>")
            {
                app.$data.sendMessageText="";      
                app.$data.emailMessageList="";    
                app.$data.sendMessageSubject="";  
            }      
                    
        },

        //send an email to all of the confirmed subjects
        sendEmailMessage:function(){

            if(app.$data.sendMessageSubject == "" )
            {
                confirm("Add a subject to your message.");
                return;
            }

            if(app.$data.sendMessageText == "" )
            {
                confirm("Your message is empty.");
                return;
            }

            if(app.$data.sendMessageButtonText == '<i class="fas fa-spinner fa-spin"></i>') return;

            app.$data.sendMessageButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {
                    action:"sendEmail", 
                    subject:app.$data.sendMessageSubject,
                    text:app.$data.sendMessageText,                                                                                                                                              
                })
                .then(function (response) {
                    //status=response.data.status;

                    if(response.data.mailResult.error_message != "")
                    {
                        app.$data.emailMessageList = "<br>Email Send Error:<br>"
                        app.$data.emailMessageList += response.data.mailResult.error_message + "<br><br>";
                    }
                    else
                    {
                        app.$data.emailMessageList =  response.data.mailResult.mail_count + " messages sent.";                                     
                    }   

                    app.$data.sendMessageButtonText = "Send Message <i class='fas fa-envelope fa-xs'></i>";                                                              
                })
                .catch(function (error) {
                    console.log(error);
                    //app.$data.searching=false;                                                              
                });
            },

        formatDate: function(value){
                if (value) {
                    //return value;
                    return moment(String(value)).local().format('M/D/YYYY, h:mm a')
                }
                else{
                    return "date format error";
                }
            },           
        
    },
    
    mounted: function(){
        $('#sendMessageModalCenter').on("hidden.bs.modal", this.hideSendMessage);
    },
});