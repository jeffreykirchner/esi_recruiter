"use strict";

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

let app = Vue.createApp({

    delimiters: ['[[', ']]'],       

    data(){return{
        calendar:[],
        todayDay:"",
        todayMonth:"",
        todayYear:"",
        currentMonth:"",
        currentYear:"",
        currentMonthString:"",
        locations:[],
        displayDay:{dayString:"",
                    no_experiments:true,
                    sessionLocations:[],
                    },
        jump_to_month : "",
        working : true,
        load_url_month : true,
        calendarDayModal : null,
    }},

    methods:{
        //get current, last or next month

        getMonth:function getMonth(){

            let load_url_month_local = false;

            if( typeof app == 'undefined')
            {
                load_url_month_local = true;
            }
            else
            {
                load_url_month_local = app.load_url_month;
                app.working = true;
            }
               
            axios.post('{{request.path}}', {
                    action :"getMonth" , 
                    load_url_month : load_url_month_local,                            
                })
                .then(function (response) {     
                    app.updateMonth(response);  

                    app.locations = response.data.locations;     
                    app.todayDay = response.data.todayDay;
                    app.todayMonth = response.data.todayMonth; 
                    app.todayYear = response.data.todayYear;           
                    
                    app.working = false;
                    app.load_url_month = false;

                    Vue.nextTick(() => {
                        app.scollToToday();
                    });
                })
                .catch(function (error) {
                    console.log(error);                            
                });                        
            },

        //get new month's data
        changeMonth:function changeMonth(direction){
            app.working = true;

            // if(direction == "next")
            // {
            //     app.forwardButtonText='<i class="fas fa-spinner fa-spin"></i>';
            // }
            // else
            // {
            //     app.backButtonText='<i class="fas fa-spinner fa-spin"></i>';
            // }

            axios.post('/calendar/', {
                    action :"changeMonth" , 
                    direction: direction,
                    currentMonth: app.currentMonth,
                    currentYear: app.currentYear,
                })
                .then(function (response) {     
                    app.updateMonth(response);
                    
                    app.working = false;

                    // app.backButtonText="<<";
                    // app.forwardButtonText=">>";
                })
                .catch(function (error) {
                    console.log(error);                            
                });                        
            },
        
        //show day modal
        showDayModal:function showDayModal(weekIndex, dayIndex, dayString){
            let currentSessions = app.calendar[weekIndex][dayIndex].sessions;

            let displayDayLocations=[];

            app.displayDay.no_experiments = true;

            for(let i=0;i<app.locations.length;i++)
            {
                let l = app.locations[i];
                let sessionList = [];

                for(let j=0;j<currentSessions.length;j++)
                {
                    if(currentSessions[j].location.id == l.id)
                    {
                        sessionList.push(currentSessions[j]);
                        app.displayDay.no_experiments = false;
                    }
                }

                displayDayLocations.push({"location":l.name,
                                            "sessions":sessionList,
                                        })
            }

            app.displayDay.sessionLocations = displayDayLocations;
            app.displayDay.dayString = dayString;

           app.calendarDayModal.show();

        },

        //jump to new month
        jump_to_new_month:function jump_to_new_month()
        {
            app.working = true;

            axios.post('/calendar/', {
                action :"jump_to_month" , 
                new_month: app.jump_to_month,
            })
            .then(function (response) {     
                app.updateMonth(response);

               app.working = false;
            })
            .catch(function (error) {
                console.log(error);                            
            }); 
        },

        //update the current month's da
        updateMonth:function updateMonth(response){
            app.currentMonth = response.data.currentMonth;
            app.currentYear = response.data.currentYear;       
            app.calendar = response.data.calendar;          
            app.currentMonthString = response.data.currentMonthString; 
            app.jump_to_month = response.data.jump_to_month;

            history.replaceState({}, null, '/calendar/' + app.currentMonth +'/' + app.currentYear + '/');

            
        },

        //scroll to today's cell
        scollToToday: function scollToToday(){
            let v = "id_" + app.todayDay + "_" + app.todayMonth + "_" + app.todayYear;
            let elmnt = document.getElementById(v);

            if(elmnt) elmnt.scrollIntoView(); 
        },
    },            

    mounted(){
        
        Vue.nextTick(() => {
            app.getMonth();  
            app.calendarDayModal = new bootstrap.Modal(document.getElementById('calendarDayModal'), {keyboard: false});                     
        });                          
    },
}).mount('#app');