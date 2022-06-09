axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = new Vue({

    delimiters: ['[[', ']]'],
    el: '#root',        
    data:{
        sessionDayUsers:[],
        payGroup:"{{payGroup|safe}}",
        payoutTotal:"",
        experiment_session_day:null,
        consentForm:{{consent_form|safe}},
    },

    methods:{

        
        //get the session day json info
        getSession:function(payGroup){           
            if(app)
            {                
                for(let i=0;i<app.$data.sessionDayUsers.length;i++)
                {
                    if(app.$data.sessionDayUsers[i].pixi_app)
                    {
                        // app.clearPixi(app.$data.sessionDayUsers[i].pixi_app, 
                        //               "signature_canvas_id_" + app.$data.sessionDayUsers[i].id );
                        
                        app.$data.sessionDayUsers[i].pixi_app.stage.removeChildren();
                        app.$data.sessionDayUsers[i].pixi_app.destroy(true,true);
                    }
                }

                app.$data.sessionDayUsers =[];
            }

            axios.post('/experimentSessionPayouts/{{id}}/'+payGroup+'/', {
                action : "getSession" ,  
                payGroup : payGroup,                                                                                                                           
            })
            .then(function (response) {     
                app.$data.sessionDayUsers = response.data.sessionDayUsers;   
                app.$data.payGroup = payGroup;
                app.$data.experiment_session_day = response.data.experiment_session_day;
                
                app.calcPayoutTotal();

                setTimeout(app.setupPixi, 500);
            })
            .catch(function (error) {
                console.log(error);                                   
            });                        
        },  

        //hide subject from list and payout total
        hideSubject:function(id,localIndex){
            u = app.$data.sessionDayUsers[localIndex];
            u.show=false;

            app.calcPayoutTotal();
        },

        //calc payout total of visible subjects
        calcPayoutTotal:function(){
            var s = 0;

            for(i=0;i<app.$data.sessionDayUsers.length;i++)
            {
                u = app.$data.sessionDayUsers[i];

                if(u.show)
                {
                    s += parseFloat(u.payout);                              
                }
            }

            app.$data.payoutTotal = s.toFixed(2);
        },

        //format date to human readable
        formatDate: function(value){
            if (value) {        
                //console.log(value);                    
                return moment(String(value)).local().format('MM/DD/YYYY hh:mm a');
            }
            else{
                return "date format error";
            }
        },

        {%include "staff/experiment_session_payouts/pixi_setup.js"%}
    },

    mounted: function(){
            this.getSession("{{payGroup}}");                    
    },
});