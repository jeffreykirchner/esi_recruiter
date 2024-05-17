"use strict";

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = Vue.createApp({

    delimiters: ['[[', ']]'],
  
    data(){return{                
        sessions:[],
        autoRefreshButtonText:'Auto Refresh: Off <i class="fas fa-sync fa-spin"></i>',
        closeAllButtonText:'Complete All Sessions <i class="fas fa-check"></i>',
        auto_refresh:"Off",
        last_refresh:"",
        timeouts:[],
        isAdmin:{%if user.is_staff%}true{%else%}false{%endif%},
    }},

    methods:{
        
        //get list of open experiments
        getOpenSessions:function getOpenSessions(){       
            
            axios.post('/sessionsOpen/', {
                            action :"getOpenSessions" ,                                                                                                                             
                        })
                        .then(function (response) {     
                            
                            app.sessions=response.data.sessions;

                            app.autoRefreshButtonText='Auto Refresh: ' + app.auto_refresh + ' <i class="fas fa-sync"></i>';
                            app.last_refresh = moment(new Date).local().format('MM/DD/YYYY hh:mm:ss a'); 

                            if(app.auto_refresh=="On")
                            {
                                app.timeouts.push(setTimeout(app.getOpenSessions, 60000));            
                            }
                            
                        })
                        .catch(function (error) {
                            console.log(error);
                            
                        });                        
        },

        autoRefreshButton:function autoRefreshButton(){
            if(app.auto_refresh == "Off")
            {
                app.auto_refresh = "On";
                this.getOpenSessions()
            }
            else
            {
                app.auto_refresh = "Off";        
                
                for (var i = 0; i < app.timeouts.length; i++) {
                    clearTimeout(app.timeouts[i]);
                }

                app.timeouts=[];
            }

            app.autoRefreshButtonText = 'Auto Refresh: ' + app.auto_refresh + ' <i class="fas fa-sync"></i>';
        },

        //get list of open experiments
        closeAllSessions:function closeAllSessions(){        
            
            var r = confirm("Are you sure you want to complete all sessions?");
            if (r == false) {
                return;
            }
            
            app.closeAllButtonText= '<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';

            axios.post('/sessionsOpen/', {
                action :"closeAllSessions" ,                                                                                                                             
            })
            .then(function (response) {     
                
                app.sessions=response.data.sessions;
                app.closeAllButtonText='Complete All Sessions <i class="fas fa-check"></i>';   

            })
            .catch(function (error) {
                console.log(error);
            
            });                        
        },

    
    },
        
    mounted(){
        this.getOpenSessions();                  
    },
    
}).mount('#app');