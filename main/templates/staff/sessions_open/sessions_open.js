axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = new Vue({

    delimiters: ['[[', ']]'],
    el: '#root',        
    data:{                
        sessions:[],
        autoRefreshButtonText:'Auto Refresh: Off <i class="fas fa-sync fa-spin"></i>',
        closeAllButtonText:'Complete All Sessions <i class="fas fa-check"></i>',
        auto_refresh:"Off",
        last_refresh:"",
        timeouts:[],
        isAdmin:{%if user.is_staff%}true{%else%}false{%endif%},
    },

    methods:{
        
        //get list of open experiments
        getOpenSessions:function(){       
            
            axios.post('/sessionsOpen/', {
                            action :"getOpenSessions" ,                                                                                                                             
                        })
                        .then(function (response) {     
                            
                            app.$data.sessions=response.data.sessions;

                            app.$data.autoRefreshButtonText='Auto Refresh: ' + app.$data.auto_refresh + ' <i class="fas fa-sync"></i>';
                            app.$data.last_refresh = moment(new Date).local().format('MM/DD/YYYY hh:mm:ss a'); 

                            if(app.$data.auto_refresh=="On")
                            {
                                app.$data.timeouts.push(setTimeout(app.getOpenSessions, 60000));            
                            }
                            
                        })
                        .catch(function (error) {
                            console.log(error);
                            
                        });                        
        },

        autoRefreshButton:function(){
            if(app.$data.auto_refresh == "Off")
            {
                app.$data.auto_refresh = "On";
                this.getOpenSessions()
            }
            else
            {
                app.$data.auto_refresh = "Off";        
                
                for (var i = 0; i < app.$data.timeouts.length; i++) {
                    clearTimeout(app.$data.timeouts[i]);
                }

                app.$data.timeouts=[];
            }

            app.$data.autoRefreshButtonText = 'Auto Refresh: ' + app.$data.auto_refresh + ' <i class="fas fa-sync"></i>';
        },

        //get list of open experiments
        closeAllSessions:function(){        
            
            var r = confirm("Are you sure you want to complete all sessions?");
            if (r == false) {
                return;
            }
            
            app.$data.closeAllButtonText= '<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';

            axios.post('/sessionsOpen/', {
                action :"closeAllSessions" ,                                                                                                                             
            })
            .then(function (response) {     
                
                app.$data.sessions=response.data.sessions;
                app.$data.closeAllButtonText='Complete All Sessions <i class="fas fa-check"></i>';   

            })
            .catch(function (error) {
                console.log(error);
            
            });                        
        },

    
    },
        
    mounted: function(){
        this.getOpenSessions();                  
    },
    
});