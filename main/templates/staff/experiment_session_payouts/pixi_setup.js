{% load static %}

/**
 * update the pixi players with new info
 */
setupPixi: function setupPixi(){    
    if(app.payGroup!="consent") return;
    if(!app.consentForm) return;
    if(!app.consentForm.signature_required) return;

    app.pixi_signature_texture = PIXI.Texture.from('{% static "signature_4.png" %}');

    if(! app.pixi_app)
    {
        app.offScreenCanvas = document.createElement("canvas");
        app.c_width = 200;
        app.c_height = 50;
        app.offScreenCanvas.width = app.c_width;
        app.offScreenCanvas.height = app.c_height;

        app.pixi_app = new PIXI.Application({
            
            width:app.c_width,
            height:app.c_height,

            antialias: true,
        
            view: app.offScreenCanvas });
    }

    app.counter=0;
    app.tick_tock=0;

    app.pixi_app.ticker.add((delta) => {       

        if(app.counter<app.sessionDayUsers.length)
        {
            if(app.tick_tock==0)
            {
                app.tick_tock=1;
                app.resetPixiApp("signature_canvas_id_" + app.sessionDayUsers[app.counter].id, 
                            app.sessionDayUsers[app.counter].profile_consent_form.signature_points,
                            app.sessionDayUsers[app.counter].profile_consent_form.singnature_resolution)
            }
            else
            {
                app.tick_tock=0;

                let canvas = document.getElementById("signature_canvas_id_" + app.sessionDayUsers[app.counter].id);
                temp_c=app.pixi_app.renderer.extract.canvas(app.pixi_app.stage);
                canvas.getContext("2d").drawImage(temp_c, 0, 0);

                app.counter++;
            }
        }
        else
        {
            app.counter=0;
            app.tick_tock=0;
        }

    
    });

    for(let i=0;i<app.sessionDayUsers.length;i++)
    {
        // if(app.sessionDayUsers[i].pixi_app)
        // {
        //     app.sessionDayUsers[i].pixi_app.destroy();
        // }
        
        
    }
},

resetPixiApp: function resetPixiApp(canvas_id, signature_points, signature_scale){
    
    app.pixi_app.stage.removeChildren()
    
    if(app.payGroup=="consent")
    for (let i in signature_points) {

        let t = signature_points[i];        

        let points = [];

        for(let j=0;j<t.length;j++)
        {
            points.push(new PIXI.Point(t[j].x,
                                       t[j].y))
        }
            
        r = new PIXI.SimpleRope(app.pixi_signature_texture, points);

        //r.scale.x = r.scale.y = app.c_height / signature_scale.height;

        app.pixi_app.stage.addChild(r);
    }    
},

//load past signature
clearPixi: function clearPixi(pixi_app,canvas_id){

    // let canvas = document.getElementById(canvas_id);

    // let background = new PIXI.Graphics();
    // background.beginFill(0xffffff);
    // background.drawRect(0, 0, canvas.width, canvas.height);
    // background.endFill();

    pixi_app.stage.removeChildren();
},

