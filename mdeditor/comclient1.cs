using System;
using System.Runtime.InteropServices;

[Guid("A4EE8981-BBD2-4482-A7CD-B754056D166C"),
    InterfaceType(ComInterfaceType.InterfaceIsDual)]
interface IMyInterface
{
void MyRun1();
void MyRun2([In] int a);
int MyRun3([In] int a);
int MyMethod( [In] int a, [In] int b);
}

[ComImport, Guid("3E9DB74C-3CB5-4735-8B3A-A3F76CF275A8")]
class mytypelib
{

}

//https://msdn.microsoft.com/zh-tw/library/aa288455(v=vs.71).aspx
class comclient1
{
  public static void Main(string[] args)
  {
    int d = 0;
     mytypelib a = new mytypelib();
     //IMyInterface im = (IMyInterface) a;
     //int[] c = new int[3];


     //im.MyMethod(1,2);
     //im.MyRun1();
     //im.MyRun2(1);

     Console.WriteLine("comclient1 start " + d);

  }
}
