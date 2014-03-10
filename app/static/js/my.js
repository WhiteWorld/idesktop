/**
 * Created by whiteworld on 12/22/13.
 */
$(document).ready(function(){
    $(document).on('click','.add_download',function(){
        var name = $(this).attr('name');
        //$('#'+name+'icon').addClass('fg-green');
        $(this).find('i').addClass('fg-green');
        $(this).removeClass('add_download');
        $(this).addClass('remove_download');
        $.get('/download/'+name+'/1/', function(){
            var $num = $('#'+name);
            //alert($num.text());
            var cur_num = parseInt($num.text(), 10);
            //alert(cur_num.toString());
            ++cur_num;
            $num.text(cur_num.toString());
        });
        return false;
    });
    $(document).on('click','.remove_download',function(){
        var name = $(this).attr('name');
        //$('#'+name+'icon').removeClass('fg-green');
        $(this).find('i').removeClass('fg-green');
        $(this).removeClass('remove_download');
        $(this).addClass('add_download');
        $.get('/download/'+name+'/2/', function(){
            var $num = $('#'+name);
            //alert($num.text());
            var cur_num = parseInt($num.text(), 10);
            //alert(cur_num.toString());
            --cur_num;
            $num.text(cur_num.toString());
        });
        return false;
    });
    $(document).on('click','.like',function(){
        var name = $(this).attr('name');
        //$('#'+name+'icon').addClass('fg-green');
        $(this).find('i').removeClass('icon-heart-2');
        $(this).find('i').addClass('fg-red icon-heart');
        $(this).removeClass('like');
        $(this).addClass('dislike');
        $.get('/like/'+name+'/1/', function(){
            var $num = $('#like'+name);
            //alert($num.text());
            var cur_num = parseInt($num.text(), 10);
            //alert(cur_num.toString());
            ++cur_num;
            $num.text(cur_num.toString());
        });
        return false;
    });
    $(document).on('click','.dislike',function(){
        var name = $(this).attr('name');
        //$('#'+name+'icon').removeClass('fg-green');
        $(this).find('i').removeClass('fg-red icon-heart');
        $(this).find('i').addClass('icon-heart-2');
        $(this).removeClass('dislike');
        $(this).addClass('like');
        $.get('/like/'+name+'/2/', function(){
            var $num = $('#like'+name);
            //alert($num.text());
            var cur_num = parseInt($num.text(), 10);
            //alert(cur_num.toString());
            --cur_num;
            $num.text(cur_num.toString());
        });
        return false;
    });
    $(document).on('click','.follow',function(){
        var name = $(this).attr('name');
        $(this).text('unfollow');
        var $num = $('#follower'+name);
        var cur_num = parseInt($num.text(), 10);
        //alert(cur_num.toString());
        ++cur_num;
        $num.text(cur_num.toString());
        $.get('/follow/'+name+'/1/', function(){
        });
        return false;
    });
    $(document).on('click','.unfollow',function(){
        var name = $(this).attr('name');
        $(this).text('follow');
        var $num = $('#follower'+name);
        var cur_num = parseInt($num.text(), 10);
        //alert(cur_num.toString());
        --cur_num;
        $num.text(cur_num.toString());
        $.get('/follow/'+name+'/2/', function(){
        });
        return false;
    });
});