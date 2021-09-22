axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = new Vue({

    delimiters: ['[[', ']]'],
    el: '#root',        
    data:{
        calendar:[],
        todayDay:"",
        todayMonth:"",
        todayYear:"",
        currentMonth:"",
        currentYear:"",
        currentMonthString:"",
        locations:[],
        displayDay:{dayString:"",
                    sessionLocations:[],
                    },
        forwardButtonText:">>",
        backButtonText:"<<",
        jump_to_month : "{{month_list.0|safe}}",
                    
    },

    methods:{
        //get current, last or next month
        getMonth:function(){
            axios.post('/calendar/', {
                    action :"getMonth" , 
                                                
                })
                .then(function (response) {     
                    app.updateMonth(response);  
                    app.$data.locations = response.data.locations;     
                    app.$data.todayDay = response.data.currentDay;
                    app.$data.todayMonth = response.data.currentMonth; 
                    app.$data.todayYear = response.data.currentYear;                      
                })
                .catch(function (error) {
                    console.log(error);                            
                });                        
            },

        //get new month's data
        changeMonth:function(direction){
            if(direction == "next")
            {
                app.$data.forwardButtonText='<i class="fas fa-spinner fa-spin"></i>';
            }
            else
            {
                app.$data.backButtonText='<i class="fas fa-spinner fa-spin"></i>';
            }

            axios.post('/calendar/', {
                    action :"changeMonth" , 
                    direction: direction,
                    currentMonth: app.$data.currentMonth,
                    currentYear: app.$data.currentYear,
                })
                .then(function (response) {     
                    app.updateMonth(response);

                    app.$data.backButtonText="<<";
                    app.$data.forwardButtonText=">>";
                })
                .catch(function (error) {
                    console.log(error);                            
                });                        
            },
        
        //show day modal
        showDayModal:function(weekIndex,dayIndex,dayString){
            currentSessions = app.$data.calendar[weekIndex][dayIndex].sessions;

            displayDayLocations=[];

            for(i=0;i<app.$data.locations.length;i++)
            {
                l = app.$data.locations[i];
                sessionList = [];

                for(j=0;j<currentSessions.length;j++)
                {
                    if(currentSessions[j].location.id == l.id)
                    {
                        sessionList.push(currentSessions[j]);
                    }
                }

                displayDayLocations.push({"location":l.name,
                                            "sessions":sessionList,
                                        })
            }

            app.$data.displayDay.sessionLocations = displayDayLocations;
            app.$data.displayDay.dayString = dayString;

            $('#calendarDayModal').modal('toggle');

        },

        //jump to new month
        jump_to_new_month:function()
        {
            axios.post('/calendar/', {
                action :"jump_to_month" , 
                direction: app.$data.jump_to_month,
            })
            .then(function (response) {     
                app.updateMonth(response);

                app.$data.backButtonText="<<";
                app.$data.forwardButtonText=">>";
            })
            .catch(function (error) {
                console.log(error);                            
            }); 
        },

        //update the current month's da
        updateMonth:function(response){
            app.$data.currentMonth = response.data.currentMonth;
            app.$data.currentYear = response.data.currentYear;       
            app.$data.calendar = response.data.calendar;          
            app.$data.currentMonthString = response.data.currentMonthString; 
        },
    },            

    mounted: function(){
            this.getMonth();                    
    },
});